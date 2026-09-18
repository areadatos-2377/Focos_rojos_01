# Blueprint 001 — Implementación inicial de Reporte Focos Rojos

> Fecha: 2026-09-18
> Estado: **pendiente de aprobación del usuario**
> Producido por: subagente `Plan` (Flujo A del Protocolo Multi-Agentes)

## Hallazgo previo: estructura real de la plantilla `.docx`

La plantilla institucional es **posicional y determinista**:

- Cuerpo: 2 párrafos de título → **Tabla 0** (portada, 2 filas × 4 celdas:
  `Estado | _ | Fecha de entrega | _` / `Responsable que llena el reporte | _ | Fecha de corte | _`)
  → párrafo de instrucciones → 5 × (párrafo `SITUACIÓN n` + **tabla de 6 filas × 2 celdas**
  etiqueta/valor).
- **Sin celdas combinadas, sin content controls, sin marcadores.**
- Las celdas de valor ya traen un `<w:p>` vacío con `rPr` apuntando a **Noto Sans**.
- El archivo pesa 7 MB porque **incrusta 5 fuentes `.odttf`** y un encabezado
  (`header2.xml`, 2.1 MB de XML) con el membrete institucional.

Esto es decisivo para las decisiones de la sección 4.

---

## 1. Estructura de carpetas

```
focos_rojos_02/
├─ .context/                    Memoria persistente
├─ legacy/                      Fuentes originales, inmutables (no se tocan nunca)
├─ backend/                     Proyecto Django + DRF
│  ├─ Dockerfile
│  ├─ requirements.txt
│  ├─ entrypoint.sh             migrate + collectstatic + gunicorn
│  ├─ manage.py
│  ├─ config/                   settings.py, urls.py, wsgi.py — configuración 12-factor
│  ├─ core/                     Transversal: scoping RBAC, permisos, cliente R2, paginación
│  ├─ usuarios/                 Usuario (AUTH_USER_MODEL), JWT, RegistroAcceso
│  ├─ catalogos/                Region, Entidad, Categoria + comando de seed
│  ├─ situaciones/              Situacion, BitacoraSituacion, services.py (orden y bitácora)
│  └─ reportes/                 ReporteGenerado, render .docx/.pdf, subida a R2
│     └─ plantillas/            Copia versionada del .docx institucional
├─ frontend/                    SPA React + Vite
│  ├─ Dockerfile
│  ├─ vite.config.js            proxy /api → backend en desarrollo
│  └─ src/
│     ├─ api/                   cliente axios + hooks de React Query por recurso
│     ├─ componentes/           UI reutilizable (fichas, badges, visor PDF, layout)
│     ├─ paginas/               una carpeta por ruta
│     ├─ contextos/             AuthContext
│     ├─ estilos/               tokens.css (verde/dorado) + base.css
│     └─ utilidades/            formato de fechas, normalización, constantes de rol
├─ docker-compose.yml           db + backend + frontend
├─ .env.example
├─ .gitignore
├─ README.md
└─ CLAUDE.md                    Convenciones para futuras sesiones
```

Apps pequeñas y por dominio; nada de capas `repositories/`, `usecases/` ni similares.
La lógica no trivial vive en `services.py` de cada app.

---

## 2. Modelo de datos

Convención: nombres de modelo y campo en español, tablas gestionadas por Django,
`BigAutoField` por defecto.

### `catalogos.Region`

| Campo | Tipo | Notas |
|---|---|---|
| `id` | BigAuto | |
| `clave` | Char(20) | `unique`. `centro`, `noreste`, … |
| `nombre` | Char(60) | `unique` |
| `orden` | PositiveSmallInt | Para listar siempre igual |

### `catalogos.Entidad`

| Campo | Tipo | Notas |
|---|---|---|
| `id` | BigAuto | |
| `clave` | Char(30) | `unique`, slug (`ciudad-de-mexico`). Va en la URL del frontend y en las llaves de R2 |
| `nombre` | Char(80) | `unique` |
| `region` | FK → Region, `PROTECT` | `related_name='entidades'`, `db_index` |
| `activa` | Bool | default `True` |

Seed fijo: 5 regiones, 24 entidades. Comando `python manage.py seed_catalogos`
idempotente (`update_or_create` por `clave`).

### `usuarios.Usuario` (extiende `AbstractUser`)

| Campo | Tipo | Notas |
|---|---|---|
| heredados | `username`, `password`, `email`, `first_name`, `last_name`, `is_active` | login por `username` |
| `nombre_completo` | Char(150) | Para mostrar; evita depender de first/last |
| `rol` | Char(15) choices `REGIONAL`/`ADMINISTRADOR`/`SUPER_ADMIN` | `db_index` |
| `region` | FK → Region, `PROTECT`, `null=True` | Obligatoria solo si `rol=REGIONAL` |
| `ultimo_acceso` | DateTime `null=True`, `db_index` | Denormalizado para la tabla de auditoría |

Constraint: un usuario regional siempre debe tener región —
`CheckConstraint(check=~Q(rol="REGIONAL") | Q(region__isnull=False))`.

`is_staff`/`is_superuser` se usan solo para el admin de Django; el RBAC de la app se basa
en `rol`. Al crear un usuario con `rol=SUPER_ADMIN` se marca `is_staff=True`.

**Crítico de secuencia:** `AUTH_USER_MODEL` debe existir *antes* del primer `migrate`.
Es el paso 5 y bloquea todo lo demás.

### `usuarios.RegistroAcceso`

| Campo | Tipo | Notas |
|---|---|---|
| `usuario` | FK → Usuario, `CASCADE` | |
| `creado_en` | DateTime `auto_now_add` | |
| `ip` | GenericIPAddress `null=True` | de `X-Forwarded-For` (Railway va detrás de proxy) |
| `user_agent` | Char(300) `blank=True` | |

Index `('usuario', '-creado_en')`. Se escribe una fila en cada login exitoso y se actualiza
`Usuario.ultimo_acceso` en la misma transacción.

### `catalogos.Categoria`

| Campo | Tipo | Notas |
|---|---|---|
| `nombre` | Char(120) | tal como lo escribió quien la creó |
| `nombre_normalizado` | Char(120) | **`unique=True`**, `editable=False` |
| `creada_por` | FK → Usuario, `SET_NULL`, `null=True` | |
| `creada_en` | DateTime `auto_now_add` | |
| `activa` | Bool default `True` | se apaga al fusionar |

Normalización en `catalogos/normalizacion.py`: descomponer con `unicodedata.normalize`
en NFKD, descartar los caracteres combinantes (quita acentos), colapsar espacios y aplicar
`casefold()`. Se calcula en `Categoria.save()` y se valida en el serializer. La unicidad la
garantiza la BD, no solo la aplicación.

**No** se usa la extensión `unaccent` de PostgreSQL: requiere `CREATE EXTENSION`
(privilegio incómodo en Railway), es más difícil de testear, y la normalización en Python
queda en un único lugar documentado. Test obligatorio que fije
`Logística` / `logistica` / `LOGÍSTICA` → mismo valor.

`POST /api/categorias/`: si el normalizado ya existe **no es error** — devuelve `200` con
la categoría existente. Así cualquiera "agrega" sin fricción y no se duplican.

### `situaciones.Situacion`

| Campo | Tipo | Notas |
|---|---|---|
| `entidad` | FK → Entidad, `PROTECT` | `related_name='situaciones'`, `db_index` |
| `categoria` | FK → Categoria, `PROTECT` | |
| `tema` | Char(300) | |
| `fecha_inicio` | Date | |
| `estatus` | Char(12) choices `ABIERTA`/`EN_PROCESO`/`CERRADA` | default `ABIERTA`, `db_index` |
| `estatus_detalle` | Text | el "Estatus actual" extenso del formato |
| `acciones` | Text | |
| `responsable` | Char(200) | texto libre |
| `fecha_estimada_solucion` | Date `null=True` | ver decisión D1 |
| `orden` | PositiveInt `null=True` | 1 = más urgente; **solo para activas** |
| `archivada_en` | DateTime `null=True`, `db_index` | se sella al cerrar |
| `creada_por` / `actualizada_por` | FK → Usuario, `SET_NULL`, `null=True` | |
| `creada_en` / `actualizada_en` | DateTime | |

Constraints e índices:

- `UniqueConstraint(fields=["entidad", "orden"], condition=Q(archivada_en__isnull=True))`
  — el orden es único solo entre activas.
- `CheckConstraint` que obliga a: activa ⇒ tiene orden; archivada ⇒ orden nulo.
- `CheckConstraint` de orden positivo.
- `Index(fields=["entidad", "archivada_en", "orden"])`.

**Orden de importancia.** Toda la lógica en `situaciones/services.py`, nunca en las vistas
ni en `save()`:

- Representación: entero **denso 1..N** entre las activas de una entidad. Se eligió entero
  denso y no fraccional/`lexorank` porque N ≤ ~15 por entidad y hay 24 entidades:
  reescribir N filas es trivial y el estado es legible.
- **Insertar:** en `transaction.atomic()` + `select_for_update()` sobre las activas de esa
  entidad, `orden = (max(orden) or 0) + 1` → entra al final y el usuario la arrastra.
- **Reordenar:** `PUT /api/entidades/{clave}/orden-situaciones/` con la lista de ids.
  Se valida que el conjunto recibido sea **exactamente** el de activas de esa entidad
  (rechaza listas parciales → evita pisar cambios de otro usuario con vista obsoleta).
  Se aplica en **dos fases dentro de una transacción**, porque un índice único parcial en
  PostgreSQL **no puede ser `DEFERRABLE`**:
  1. desplazar todas las activas sumando 10000 (siguen siendo únicas y positivas);
  2. `bulk_update` asignando 1..N según la lista recibida.

  No genera bitácora (regla explícita de `productContext.md`).
- **Cerrar:** `archivada_en = now()`, `orden = None`, y se **densifica** el resto (1..N sin
  huecos) con la misma técnica. La fila cerrada sale del índice único parcial y de la galería.
- **Reabrir:** `archivada_en = None`, `orden = max+1`, bitácora `REAPERTURA`.
- **Cambio de entidad:** no se permite en v1 (solo lectura tras crear); evita densificar
  dos entidades a la vez.

### `situaciones.BitacoraSituacion`

Formato **campo a campo**, no snapshot: `productContext.md` pide literalmente "quién,
cuándo, qué campo, valor anterior y nuevo", se renderiza directo como línea de tiempo sin
diffing en el cliente, y el volumen no justifica copias completas.

| Campo | Tipo | Notas |
|---|---|---|
| `situacion` | FK → Situacion, `CASCADE` | `related_name='bitacora'` |
| `usuario` | FK → Usuario, `SET_NULL`, `null=True` | |
| `creado_en` | DateTime `auto_now_add` | |
| `accion` | Char(20) choices `CREACION`/`EDICION`/`CAMBIO_ESTATUS`/`CIERRE`/`REAPERTURA` | |
| `campo` | Char(40) `blank=True` | nombre técnico (`tema`, `acciones`, …) |
| `valor_anterior` | Text `null=True` | |
| `valor_nuevo` | Text `null=True` | |

Index `('situacion', '-creado_en')`.

Reglas de escritura:

- Creación → **una sola fila** `accion=CREACION`, sin campo.
- Edición → **una fila por campo modificado**, comparando contra la versión en BD dentro
  de la transacción.
- Los valores se guardan **ya renderizados como texto humano** (`categoria` → su nombre,
  fechas en ISO, `estatus` → su etiqueta). Así la bitácora sobrevive a un renombrado o
  fusión de categorías.
- Excluidos siempre: `orden`, `archivada_en`, `actualizada_en`, `actualizada_por`.
- La etiqueta legible del campo se resuelve en el serializer con un diccionario, no en BD.

Visibilidad: mismo alcance que la situación (hereda el mixin de scoping), no solo admins.

### `reportes.ReporteGenerado`

| Campo | Tipo | Notas |
|---|---|---|
| `id` | UUID, `primary_key`, default `uuid4` | se usa en la llave de R2 y en la URL; no enumerable |
| `entidad` | FK → Entidad, `PROTECT`, `db_index` | |
| `version` | PositiveInt | consecutivo **por entidad** (v1, v2…) |
| `generado_por` | FK → Usuario, `PROTECT` | los usuarios se desactivan, no se borran |
| `generado_en` | DateTime `auto_now_add`, `db_index` | |
| `fecha_entrega` | Date | dato de portada |
| `responsable_reporte` | Char(200) | dato de portada |
| `fecha_corte` | Date | dato de portada |
| `r2_key_docx` / `r2_key_pdf` / `r2_key_json` | Char(300) | |
| `bytes_docx` / `bytes_pdf` | PositiveInt | tamaño mostrado en el historial |
| `sha256_docx` | Char(64) | integridad |

`UniqueConstraint(fields=["entidad", "version"])`. La versión se calcula con
`select_for_update()` sobre los reportes previos de esa entidad dentro de la transacción.

### `reportes.ReporteSituacion` (tabla intermedia explícita)

| Campo | Tipo |
|---|---|
| `reporte` | FK → ReporteGenerado, `CASCADE` |
| `situacion` | FK → Situacion, `PROTECT` |
| `posicion` | PositiveSmallInt (1..5) |

Constraints: `unique(reporte, posicion)`, `unique(reporte, situacion)`, y posición en 1..5.

Mantener la FK además del JSON permite responder "¿en qué reportes apareció esta
situación?" sin abrir R2. El texto inmutable vive en el JSON; la FK es solo trazabilidad.

**Inmutabilidad:** sin acciones `destroy` ni `update` en el ViewSet de reportes, y el token
de R2 se emite **sin permiso de borrado** (defensa en profundidad).

---

## 3. API REST

Prefijo `/api/`. Autenticación JWT (`rest_framework_simplejwt`).
`DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]` y
`DEFAULT_AUTHENTICATION_CLASSES = [JWTAuthentication]` — nada es público por omisión.

### Autenticación y perfil

| Método | Ruta | Rol | Propósito |
|---|---|---|---|
| POST | `/api/auth/login/` | público | Devuelve `access`+`refresh`+perfil; escribe `RegistroAcceso` y `ultimo_acceso` |
| POST | `/api/auth/refresh/` | público | Renueva el `access` |
| POST | `/api/auth/logout/` | autenticado | Invalida el `refresh` (blacklist) |
| GET | `/api/auth/yo/` | autenticado | Perfil, rol, región y entidades visibles |
| POST | `/api/auth/cambiar-password/` | autenticado | Cambio de contraseña propia |

### Catálogos

| Método | Ruta | Rol | Propósito |
|---|---|---|---|
| GET | `/api/regiones/` | autenticado | Regiones visibles (el regional recibe solo la suya) |
| GET | `/api/entidades/` | autenticado | Entidades del alcance, con conteo de situaciones por estatus |
| GET | `/api/entidades/{clave}/` | autenticado | Resumen de una entidad |
| POST | `/api/categorias/` | autenticado | Crea; si el normalizado ya existe devuelve la existente (200) |
| PATCH | `/api/categorias/{id}/` | super_admin | Renombrar |
| DELETE | `/api/categorias/{id}/` | super_admin | Solo si no tiene situaciones; si las tiene → 409 |
| POST | `/api/categorias/{id}/fusionar/` | super_admin | Reasigna situaciones al destino y desactiva la origen |

### Situaciones

| Método | Ruta | Rol | Propósito |
|---|---|---|---|
| GET | `/api/situaciones/` | alcance | Filtros `?entidad=&estatus=&categoria=&archivadas=&q=` (por defecto **excluye** archivadas) |
| POST | `/api/situaciones/` | alcance | Crea al final del orden + bitácora `CREACION` |
| GET/PATCH | `/api/situaciones/{id}/` | alcance | Detalle y edición con bitácora campo a campo |
| POST | `/api/situaciones/{id}/cerrar/` | alcance | Archiva y densifica el orden restante |
| POST | `/api/situaciones/{id}/reabrir/` | alcance | Vuelve a activa, al final del orden |
| GET | `/api/situaciones/{id}/bitacora/` | alcance | Historial completo, orden descendente |
| PUT | `/api/entidades/{clave}/orden-situaciones/` | alcance | Reordena todas las activas de la entidad |

### Reportes

| Método | Ruta | Rol | Propósito |
|---|---|---|---|
| POST | `/api/reportes/vista-previa/` | alcance | Devuelve `application/pdf` en línea; **no persiste nada** |
| POST | `/api/reportes/` | alcance | Genera, sube a R2 y crea la versión (201 con metadatos) |
| GET | `/api/reportes/` | alcance | Historial con filtros `?entidad=&region=&desde=&hasta=` |
| GET | `/api/reportes/{uuid}/` | alcance | Metadatos + snapshot de la versión |
| GET | `/api/reportes/{uuid}/descargar/?formato=docx\|pdf\|json` | alcance | 302 a URL prefirmada de R2 (5 min) |

Sin `PATCH` ni `DELETE`: las versiones son inmutables.

### Administración y auditoría

| Método | Ruta | Rol | Propósito |
|---|---|---|---|
| GET | `/api/usuarios/` | administrador, super_admin | Listado con `ultimo_acceso` |
| POST / PATCH | `/api/usuarios/`, `/api/usuarios/{id}/` | super_admin | Alta y edición de cuentas |
| POST | `/api/usuarios/{id}/resetear-password/` | super_admin | Asigna contraseña temporal |
| GET | `/api/auditoria/accesos/` | administrador, super_admin | Bitácora de inicios de sesión |

### RBAC por región, en un solo punto

Dos piezas, ambas en `core/`, y **ningún viewset repite la regla**:

**a) Lectura — `core/scoping.py` + `core/mixins.py`.** Una función `entidades_visibles(usuario)`
devuelve el queryset de entidades activas, filtrado por `region_id` si el rol es `REGIONAL`.
Un `AlcanceEntidadMixin` sobreescribe `get_queryset()` y filtra por esa lista; cada viewset
solo declara su ruta al FK en `lookup_entidad`:

- `'entidad'` → `Situacion`, `ReporteGenerado`
- `'situacion__entidad'` → `BitacoraSituacion`
- `None` → el propio `EntidadViewSet`

Como el filtro está en `get_queryset()`, cubre a la vez `list`, `retrieve`, `update` y las
`@action`. Un objeto fuera de alcance devuelve **404**, no 403 (no filtra la existencia de
datos ajenos).

**b) Escritura — `core/fields.py`.** Un `EntidadPermitidaField(SlugRelatedField)` cuyo
`get_queryset()` devuelve `entidades_visibles(request.user)`. Cualquier serializer que reciba
una entidad usa este campo, y DRF rechaza automáticamente una entidad fuera de alcance como
error de validación. No hay comprobaciones de rol dispersas en las vistas.

**c) Red de seguridad.** Un test de meta-nivel recorre el router de `config/urls.py` y falla
si algún viewset con modelo ligado a `Entidad` no hereda `AlcanceEntidadMixin`. Cuesta 20
líneas y evita el agujero típico al añadir un endpoint nuevo meses después.

Roles duros (no de alcance) en `core/permissions.py`: `EsAdministradorOSuperAdmin`,
`EsSuperAdmin`.

---

## 4. Generación del reporte

### Rellenado del `.docx` — recomendación: **`python-docx`** (no `docxtpl`)

Motivos derivados de la inspección del archivo:

1. **La plantilla no tiene marcadores.** Las 24 celdas de valor están vacías. Con `docxtpl`
   habría que **editar el archivo institucional en Word** para insertar marcadores, creando
   un derivado que mantener; `legacy/` dejaría de ser la única fuente de verdad y cada
   reedición en Word puede reescribir el `fontTable`, las fuentes incrustadas o el membrete
   de 2.1 MB.
2. **La estructura es fija y posicional** (Tabla 0 = portada; Tablas 1..5 = situaciones;
   siempre 6 filas). No hay listas de longitud variable: el formato es "Top 5" y los bloques
   sobrantes se dejan en blanco. El valor diferencial de `docxtpl` (bucles y condicionales
   Jinja) no aplica.
3. **Menos dependencias**: `docxtpl` arrastra `jinja2` + `python-docx` de todos modos.
4. `python-docx` **preserva el paquete OPC completo** al reabrir y guardar: encabezados,
   `media/*.png`, fuentes `.odttf` y `webextensions` sobreviven intactos.

Implementación en `reportes/plantilla.py`: dos mapas posicionales constantes.

- Portada (tabla 0): estado → celda (0,1); fecha de entrega → (0,3);
  responsable → (1,1); fecha de corte → (1,3).
- Situación (tablas 1..5): filas en orden `categoria`, `tema`, `fecha_inicio`,
  `estatus_actual`, `acciones`, `responsable_fecha`; el valor va siempre en la celda 1.

Helper obligatorio `escribir_celda(celda, texto)` — **no usar `cell.text = …`**, que borra el
`pPr`/`rPr` y pierde la fuente Noto Sans y el espaciado. En su lugar: tomar el primer párrafo
de la celda, añadir un `run`, y copiar con `copy.deepcopy` el `rPr` que ya vive en el `pPr` de
ese párrafo al `rPr` del run. Los saltos de línea del texto largo se insertan como `w:br`
dentro del mismo run, para no alterar la altura de fila con párrafos nuevos.

Concatenaciones al renderizar (no se guardan así en BD):

- `responsable_fecha` = `"{responsable} / {fecha_estimada:%d/%m/%Y}"` (regla explícita de
  `productContext.md`).
- `estatus_actual` = propuesta `"{etiqueta_estatus} — {estatus_detalle}"` → ver decisión **D7**.
- Fechas en `%d/%m/%Y`, zona `America/Mexico_City`.

**Test de blindaje** (`reportes/tests/test_plantilla.py`): abre la plantilla y afirma 6 tablas,
la primera de 2×4 y las otras de 6×2, y que las etiquetas de la columna 0 coinciden con las
esperadas. Si alguien sustituye el `.docx`, el fallo es inmediato y claro, no un reporte en
blanco en producción.

### PDF — recomendación: **LibreOffice headless dentro de la imagen del backend**

| Opción | Fidelidad | Coste en la imagen Docker | Veredicto |
|---|---|---|---|
| **LibreOffice headless en el backend** | Alta (renderiza membrete, tablas y fuentes reales) | `libreoffice-writer` + `fonts-noto-core` ≈ **+700 MB**, build más lento | **Recomendada** |
| Gotenberg como servicio aparte | Igual (envuelve LibreOffice) | Backend delgado, pero **un servicio más** en Compose y en Railway | Plan B (ver riesgo R1) |
| `docx2pdf` | Alta | Requiere **MS Word instalado** | Descartada: no corre en Linux |
| Reconstruir con ReportLab/WeasyPrint | Baja | Mínimo | Descartada: obliga a mantener un segundo diseño del formato, se desincroniza |

En el Dockerfile del backend (`python:3.12-slim`) se instalan `libreoffice-writer` y
`fonts-noto-core`. Esta última es **indispensable**: la plantilla pide **Noto Sans** y, aunque
el `.docx` incrusta las fuentes en formato `.odttf`, LibreOffice no garantiza usar fuentes
OOXML incrustadas. Sin ellas, la sustitución cambia el salto de línea y desborda celdas.

`reportes/pdf.py` invoca `soffice --headless --norestore --convert-to pdf:writer_pdf_Export`
con `timeout=60`, y — detalle crítico — un **perfil de usuario aislado por invocación** vía
`-env:UserInstallation=file:///tmp/lo_<uuid>`. Eso evita el fallo clásico de LibreOffice
cuando varios workers convierten a la vez. Gunicorn con `--timeout 120 --workers 2 --threads 4`.
Conversión **síncrona** dentro del request, conforme a `techContext.md`: 5 situaciones,
~20 usuarios, ninguna cola.

### Vista previa

`POST /api/reportes/vista-previa/` ejecuta **exactamente el mismo pipeline** que el guardado
(construir contexto → render docx → docx a pdf) y devuelve el PDF con
`Content-Type: application/pdf` y `Content-Disposition: inline`, **sin escribir en BD ni en
R2**. El frontend lo consume como `blob` y lo muestra en un `<iframe>` con
`URL.createObjectURL`. Así "lo que ves es lo que se guarda" con una sola implementación; el
arranque en frío de LibreOffice (~2–4 s) se cubre con un estado de carga. Se descarta una
previsualización HTML paralela porque sería una segunda fuente de verdad que se desincroniza.

---

## 5. Integración con R2

`core/r2.py` — cliente `boto3` **único a nivel de módulo** (un `client`, no un `resource`;
seguro entre hilos según `techContext.md`) con timeouts explícitos obligatorios:
`connect_timeout=10`, `read_timeout=20`, `retries={"max_attempts": 2}`,
`signature_version="s3v4"`, `region_name="auto"`.

### Convención de llaves

```
reportes/{entidad_clave}/{YYYY}/{uuid}/reporte.docx
reportes/{entidad_clave}/{YYYY}/{uuid}/reporte.pdf
reportes/{entidad_clave}/{YYYY}/{uuid}/snapshot.json
```

Ejemplo: `reportes/ciudad-de-mexico/2026/8f3c…a91/reporte.pdf`.

El prefijo por entidad y año permite listar y aplicar reglas de ciclo de vida por entidad sin
consultar la BD. El nombre de archivo **amigable** no va en la llave sino en la descarga, vía
`ResponseContentDisposition` de la URL prefirmada:
`focos-rojos_ciudad-de-mexico_2026-08-14_v3.pdf`. Así la llave nunca depende de datos que
puedan cambiar.

Subida: `put_object` con `ContentType` correcto y `Metadata` (`entidad`, `version`,
`generado_por`, `uuid`). Los tres objetos se suben **antes** de confirmar la transacción de
BD; si falla una subida se hace rollback y se devuelve 502 (queda a lo sumo un objeto huérfano
en R2, inofensivo y detectable por el prefijo sin fila asociada).

### Contenido del `snapshot.json`

Incluye: versión de formato, bloque `reporte` (uuid, versión, fecha, quién lo generó),
bloque `entidad` (clave, nombre, región), bloque `portada` (los 4 datos iniciales), la lista
`situaciones` con todos los campos de cada una, y el bloque `archivos` con las llaves, el
sha256 y los tamaños.

Cada situación guarda además **el texto literal que se imprimió en cada celda**
(`texto_celda_estatus`, `texto_celda_responsable_fecha`), no solo los datos crudos: así una
auditoría futura puede reconstruir el documento sin depender de la lógica de renderizado
vigente.

### Descarga de una versión histórica

`GET /api/reportes/{uuid}/descargar/?formato=pdf` → el viewset (con el mixin de alcance, así
que un regional no ve versiones de otra región) genera una **URL prefirmada de 5 minutos** y
responde **302**. Nunca se proxean los bytes por Django: ahorra tiempo de worker y memoria.

---

## 6. Frontend

### Rutas (`react-router-dom` v6)

| Ruta | Contenido |
|---|---|
| `/login` | Formulario de acceso |
| `/` | Redirección por rol |
| `/entidades` | Admins: tarjetas **agrupadas por región**. Regional: lista plana de sus entidades |
| `/entidades/:clave` | **Galería de situaciones**: fichas arrastrables, filtros por estatus/categoría, alternador "Archivadas", botones "Nueva situación" y "Generar Reporte Focos Rojos" |
| `/entidades/:clave/situaciones/:id` | Detalle + línea de tiempo de la bitácora (panel lateral con URL propia) |
| `/entidades/:clave/reporte` | Asistente de 3 pasos: portada → selección (máx. 5) → vista previa y guardar |
| `/reportes` | Historial de versiones con filtros y descarga `.docx` / `.pdf` / `.json` |
| `/admin/usuarios` | super_admin |
| `/admin/categorias` | super_admin (renombrar, fusionar, eliminar) |
| `/admin/accesos` | administrador + super_admin |

### Componentes principales

`LayoutApp` (barra lateral con degradado verde→dorado tomada del mockup), `TarjetaEntidad`,
`GaleriaSituaciones`, `FichaSituacion` (arrastrable, muestra número de orden, badge de estatus
y categoría), `FormularioSituacion` (`react-hook-form` + `zod`), `SelectorCategoria` (combo con
opción "Crear «…»"), `LineaTiempoBitacora`, `AsistenteReporte`, `VisorPdf`, `TablaVersiones`,
`BadgeEstatus`, `ChipFiltro`, `RutaProtegida` / `RutaPorRol`.

### Estado

- **Servidor: TanStack Query (React Query)**. Cachea entidades y categorías (casi estáticas) y
  situaciones por entidad; invalidación por clave `['situaciones', claveEntidad]`. Cubre
  reintentos, estados de carga y actualización optimista sin escribir un reducer.
- **Sesión: `AuthContext`** con `access` **en memoria** y `refresh` en `localStorage`;
  interceptor de axios que renueva ante un 401 y reintenta una vez. Ver decisión **D9**.
- **Nada de Redux ni Zustand**: no hay estado global compartido más allá de la sesión.

### Arrastrar y soltar — recomendación: **`@dnd-kit/core` + `@dnd-kit/sortable`**

`react-beautiful-dnd` está descontinuado y da problemas con React 18 en `StrictMode`.
`@dnd-kit` está mantenido, es ligero, sin dependencias, trae **accesibilidad por teclado**
(importante para un sistema institucional) y su `rectSortingStrategy` encaja con una galería
de fichas en rejilla. Patrón: `arrayMove` local → `useMutation` optimista contra
`PUT /orden-situaciones/` → `onError` restaura el orden previo del caché y muestra un aviso.

### Estilos

`src/estilos/tokens.css` levantado casi textualmente del mockup, con el **verde como color
primario y el dorado como acento** (`--verde:#1E5B4F`, `--verde-d:#002F2A`, `--verde-l:#2E8A77`,
`--dorado:#A57F2C`, `--dorado-l:#D4AC4E`), eliminando las variables `--guinda-*`.
**CSS Modules** por componente (el mockup es CSS plano y se traslada casi sin traducción).
Tipografías Fraunces / Manrope / JetBrains Mono desde Google Fonts. Toda la interfaz en
español, incluidos los mensajes de error de la API.

---

## 7. Pasos de implementación

### Fase 0 — Andamiaje
*Verificable: `docker compose up` levanta los tres servicios; se ve el admin de Django y la SPA vacía.*

| # | Paso | Archivos | Depende | Complejidad |
|---|---|---|---|---|
| 1 | `git init`, `.gitignore` (incluye `.env`), `README.md`, `.env.example` con todas las variables | raíz | — | Baja |
| 2 | Proyecto Django `config` + `requirements.txt` + settings 12-factor (`django-environ`) + `entrypoint.sh` + `Dockerfile` | `backend/**` | 1 | Media |
| 3 | `docker-compose.yml`: `db` (postgres:16 + volumen), `backend`, `frontend`; healthcheck de la BD | `docker-compose.yml` | 2 | Media |
| 4 | Scaffold Vite React + proxy `/api` → backend | `frontend/**` | 3 | Baja |

### Fase 1 — Identidad, catálogos y RBAC
*Verificable: login desde la SPA; `/api/auth/yo/` devuelve el rol y sus entidades; un regional no ve otras regiones.*

| # | Paso | Archivos | Depende | Complejidad |
|---|---|---|---|---|
| 5 | App `usuarios`: modelo `Usuario`, `AUTH_USER_MODEL`, migración inicial. **Bloquea todas las demás migraciones** | `backend/usuarios/models.py`, `config/settings.py` | 2 | Media |
| 6 | App `catalogos`: `Region`, `Entidad`, `Categoria` (+ `normalizacion.py`) y comando `seed_catalogos` con las 5 regiones y 24 entidades | `backend/catalogos/**` | 5 | Baja |
| 7 | SimpleJWT: login/refresh/logout/yo/cambiar-password; `RegistroAcceso` + `ultimo_acceso` en el login | `backend/usuarios/**` | 6 | Media |
| 8 | **`core/scoping.py`, `core/mixins.py`, `core/fields.py`, `core/permissions.py`** + tests de alcance + meta-test del router | `backend/core/**` | 6 | Media |
| 9 | Endpoints de regiones, entidades y categorías (creación idempotente por nombre normalizado) | `backend/catalogos/**` | 8 | Media |

### Fase 2 — Situaciones y bitácora
*Verificable: CRUD completo por API; reordenar, cerrar y reabrir dejan el orden denso y correcto; la bitácora refleja cada cambio de campo.*

| # | Paso | Archivos | Depende | Complejidad |
|---|---|---|---|---|
| 10 | Modelos `Situacion` y `BitacoraSituacion` con constraints e índices | `backend/situaciones/models.py` | 6 | Media |
| 11 | `situaciones/services.py`: crear, actualizar (diff campo a campo), cerrar, reabrir, reordenar y densificar (dos fases, `select_for_update`) | `backend/situaciones/services.py` | 10 | **Alta** |
| 12 | Serializers, ViewSets, filtros y endpoint `PUT /entidades/{clave}/orden-situaciones/` | `backend/situaciones/**` | 11, 8 | Media |
| 13 | Tests: orden en las 4 operaciones, concurrencia básica, RBAC por rol, contenido de la bitácora | `backend/situaciones/tests/**` | 12 | Media |

### Fase 3 — Frontend operativo
*Verificable: el usuario entra, elige entidad, ve la galería, crea/edita una situación y reordena arrastrando.*

| # | Paso | Archivos | Depende | Complejidad |
|---|---|---|---|---|
| 14 | Cliente axios + interceptores + React Query + `AuthContext` + rutas protegidas por rol | `frontend/src/{api,contextos}/**` | 7 | Media |
| 15 | `tokens.css` (verde/dorado), `LayoutApp` con barra lateral, tipografías | `frontend/src/estilos/**` | 14 | Baja |
| 16 | Pantalla `/entidades` (agrupada por región vs. lista plana según rol) | `frontend/src/paginas/Entidades/**` | 15, 9 | Baja |
| 17 | Galería con `@dnd-kit` + actualización optimista del orden + filtros y alternador "Archivadas" | `frontend/src/paginas/Galeria/**` | 16, 12 | **Alta** |
| 18 | Formulario de situación, `SelectorCategoria` creatable, panel de bitácora | `frontend/src/paginas/Galeria/**` | 17 | Media |

### Fase 4 — Generación del reporte
*Verificable: el asistente muestra la vista previa en PDF y permite descargar el `.docx` sin guardar.*

| # | Paso | Archivos | Depende | Complejidad |
|---|---|---|---|---|
| 19 | Copiar la plantilla a `backend/reportes/plantillas/`; `reportes/plantilla.py` (mapa posicional, `escribir_celda`) + `reportes/contexto.py`; test de estructura del `.docx` | `backend/reportes/**` | 10 | **Alta** |
| 20 | Dockerfile: `libreoffice-writer` + `fonts-noto-core`; `reportes/pdf.py` con perfil aislado y timeout; **comparar visualmente el PDF contra el Word original** | `backend/Dockerfile`, `backend/reportes/pdf.py` | 19 | Media/Alta |
| 21 | `POST /api/reportes/vista-previa/` + `AsistenteReporte` (3 pasos) + `VisorPdf` | `backend/reportes/views.py`, `frontend/src/paginas/Reporte/**` | 20, 18 | **Alta** |

### Fase 5 — Versiones en R2
*Verificable: "Guardar versión" sube los 3 objetos y el historial permite descargarlos.*

| # | Paso | Archivos | Depende | Complejidad |
|---|---|---|---|---|
| 22 | `core/r2.py` (cliente boto3 con timeouts) + variables de entorno + comando `probar_r2` | `backend/core/r2.py` | 2 | Baja |
| 23 | `ReporteGenerado` + `ReporteSituacion` + `reportes/services.py::guardar_version` (docx+pdf+json, versión consecutiva, transacción) | `backend/reportes/**` | 22, 21 | Media |
| 24 | Endpoints de listado, detalle y `descargar` (302 a URL prefirmada) | `backend/reportes/**` | 23, 8 | Media |
| 25 | Pantalla `/reportes` (historial, filtros, descargas) | `frontend/src/paginas/Reportes/**` | 24 | Media |

### Fase 6 — Administración y auditoría
*Verificable: el super_admin crea una cuenta y fusiona categorías; el administrador consulta los últimos accesos.*

| # | Paso | Archivos | Depende | Complejidad |
|---|---|---|---|---|
| 26 | CRUD de usuarios (super_admin) + reseteo de contraseña + pantalla | `backend/usuarios/**`, `frontend/src/paginas/Admin/Usuarios/**` | 14 | Media |
| 27 | Renombrar / fusionar / eliminar categorías + pantalla | `backend/catalogos/**`, `frontend/src/paginas/Admin/Categorias/**` | 26 | Media |
| 28 | `/api/auditoria/accesos/` + pantalla de últimos accesos | `backend/usuarios/**`, `frontend/src/paginas/Admin/Accesos/**` | 26 | Baja |

### Fase 7 — Despliegue
*Verificable: la URL de Railway funciona de punta a punta con datos reales.*

| # | Paso | Archivos | Depende | Complejidad |
|---|---|---|---|---|
| 29 | Settings de producción: `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, CORS, WhiteNoise para los estáticos del admin, logging a stdout | `backend/config/settings.py` | Fase 6 | Media |
| 30 | Railway: PostgreSQL + servicio backend por Dockerfile + variables + `migrate` y `seed_catalogos` en el arranque | `backend/entrypoint.sh`, `railway.json` | 29 | Media |
| 31 | Servicio de frontend en Railway (build de Vite servido por nginx/Caddy) apuntando a la URL del backend | `frontend/Dockerfile`, `nginx.conf` | 30 | Media |
| 32 | Prueba de humo end-to-end + actualización de `.context/progress.md` y `activeContext.md` | `.context/**` | 31 | Baja |

---

## 8. Riesgos y decisiones abiertas

### Riesgos

- **R1 — Tamaño y tiempo de build de la imagen con LibreOffice (~+700 MB).** Si Railway
  penaliza el build o el arranque en frío, el plan B es mover la conversión a un servicio
  **Gotenberg** aparte y dejar el backend delgado; el cambio está aislado en `reportes/pdf.py`
  (una función), así que migrar después es barato. *Mitigación desde el día 1: mantener la
  conversión detrás de esa única función.*
- **R2 — Fidelidad del PDF.** La plantilla incrusta 5 fuentes `.odttf` y su encabezado
  (`header2.xml`, 2.1 MB con el membrete institucional) es gráficamente complejo. LibreOffice
  puede no honrar las fuentes incrustadas de OOXML. *Mitigación: instalar `fonts-noto-core` y,
  en el paso 20, comparar visualmente el PDF generado contra el Word original antes de
  avanzar.* Si el encabezado se degrada, hay que decidir entre aceptarlo o sustituirlo por
  una imagen.
- **R3 — LibreOffice concurrente.** Dos peticiones simultáneas pueden chocar por el perfil de
  usuario. Mitigado con `-env:UserInstallation` único por invocación; no omitir ese detalle.
- **R4 — Migración inicial con `AUTH_USER_MODEL`.** Si se corre `migrate` antes del paso 5,
  hay que borrar el volumen de PostgreSQL y las migraciones y empezar de nuevo. Es el error
  de secuencia más caro del plan.
- **R5 — Índice único parcial no diferible.** PostgreSQL no admite `DEFERRABLE` en un índice
  único parcial; por eso el reordenamiento va en dos fases con desplazamiento `+10000`. Un
  `bulk_update` ingenuo fallará con violación de unicidad.
- **R6 — Respaldos.** Railway ofrece respaldos de PostgreSQL según el plan; conviene
  confirmarlo, porque la BD es la única fuente de las situaciones (R2 solo guarda reportes
  emitidos).

### Decisiones que el usuario debe cerrar

| # | Decisión | Propuesta por omisión |
|---|---|---|
| D1 | ¿`responsable` y `fecha_estimada_solucion` son obligatorios al crear una situación? | `responsable` obligatorio, fecha opcional; en el reporte se imprime solo el responsable si falta la fecha |
| D2 | ¿Se pueden **incluir situaciones CERRADAS** en un reporte? | No: solo activas |
| D3 | ¿Existe **borrado** de situaciones o solo cierre? | Solo cierre (archivado); sin `DELETE` en la API |
| D4 | Al crear una situación, ¿entra **al final** del orden o el usuario elige posición? | Al final; se reordena arrastrando |
| D5 | Si la entidad tiene **menos de 5 situaciones**, ¿los bloques sobrantes se dejan en blanco o se eliminan las tablas? | Se dejan en blanco (el formato es fijo) |
| D6 | ¿Se permite generar **dos versiones idénticas** seguidas para la misma entidad? | Sí; el versionado es incremental y sin restricciones |
| D7 | ¿Qué texto va en la celda **"Estatus actual"**? | `"{Etiqueta del estatus} — {detalle}"`. Alternativa: solo el detalle |
| D8 | **Contraseña inicial** de las cuentas creadas por el super_admin: ¿cambio forzado en el primer acceso? | Temporal mostrada una vez, sin forzar el cambio en v1 |
| D9 | Manejo del token: `refresh` en `localStorage` vs. cookie `httpOnly` | `localStorage`, dado que son ~20 usuarios internos |
| D10 | Frontend: **segundo servicio en Railway** (nginx) o servido por Django con WhiteNoise | Segundo servicio; mantiene el build de Vite limpio |
| D11 | Estilos: **CSS Modules** vs. Tailwind | CSS Modules (traslada el mockup casi literal) |
| D12 | Bucket de R2: ¿versionado u Object Lock al crearlo? ¿token **sin permiso de borrado**? | Token sin borrado; versionado no necesario |
| D13 | Zona horaria y formato de fecha del documento | `America/Mexico_City`, `dd/mm/aaaa` |
| D14 | Retención del historial de accesos (`RegistroAcceso` crece indefinidamente) | Sin purga en v1; revisar al año |

---

## Archivos críticos para la implementación

- `legacy/Formato_Focos_Rojos_Gira_INSTITUCIONAL.docx` — plantilla fuente; su estructura
  posicional (tabla 0 = portada 2×4; tablas 1–5 = situaciones 6×2) define todo el paso 19.
- `backend/core/scoping.py` — punto único del filtro RBAC por región (con `core/mixins.py`
  y `core/fields.py`).
- `backend/situaciones/services.py` — toda la lógica de orden denso y de bitácora campo a campo.
- `backend/reportes/plantilla.py` — mapa posicional y escritura de celdas preservando formato.
- `backend/Dockerfile` — decisión de LibreOffice + `fonts-noto-core`, que condiciona la imagen
  y el despliegue.
