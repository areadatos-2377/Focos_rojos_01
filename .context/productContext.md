# Product Context — Reglas de negocio y flujos

## Catálogo de regiones y entidades

5 regiones, 24 entidades. Cada entidad pertenece a **una sola** región. Catálogo fijo (seed).

| Región | Entidades |
|---|---|
| Centro | Ciudad de México, Estado de México, Hidalgo |
| Noreste | San Luis Potosí, Tamaulipas, Veracruz, Zacatecas |
| Noroeste | Baja California, Baja California Sur, Colima, Nayarit, Sinaloa, Sonora |
| Sureste | Campeche, Chiapas, Oaxaca, Quintana Roo, Tabasco, Yucatán |
| Suroeste | Guerrero, Michoacán, Morelos, Puebla, Tlaxcala |

## La Situación (entidad central)

Campos, derivados del formato institucional:

| Campo | Tipo | Notas |
|---|---|---|
| Entidad | FK | Define quién puede verla (RBAC) |
| Categoría | FK a catálogo | Lista desplegable ampliable |
| Tema | texto largo | **No es un título**: en el formato real enumera varios puntos con cifras |
| Fecha de inicio | fecha, **opcional** | En la práctica suele dejarse en blanco |
| Estatus (clave) | enum `ABIERTA` / `EN_PROCESO` / `CERRADA` | Sirve para agrupar y contar |
| Estatus (detalle) | texto largo | El comentario extenso del formato |
| Acciones que se están realizando | texto largo | |
| Responsable | texto libre | **No** es usuario del sistema. Suele ser un área ("Coordinación de Finanzas"), no una persona |
| Fecha estimada de solución | fecha | |
| Orden de importancia | entero | 1 = más urgente, por entidad |

**Responsable y fecha estimada se guardan separados** y se concatenan solo al renderizar el
reporte, porque en el formato Word son una sola celda.

### Ciclo de vida

- Las situaciones `CERRADA` se **archivan**: salen de la galería por defecto y solo aparecen
  al consultarlas explícitamente (filtro "Archivadas").
- El orden de importancia aplica entre las situaciones activas de una entidad.

### Bitácora

Cada situación guarda su historial de cambios (quién, cuándo, qué campo, valor anterior y
nuevo). **Visible para cualquier usuario que pueda ver esa situación**, no solo admins.
El reordenamiento de fichas **no** se registra en bitácora.

## Reglas de acceso (RBAC)

- `regional`: solo las entidades de su región. Ve, registra, edita, reordena y genera reportes.
- `administrador` y `super_admin`: todas las entidades.
- Las cuentas las crea **únicamente** el `super_admin`.
- Cualquier usuario con acceso a una entidad puede reordenar sus fichas.

### Vistas según rol

- `regional`: ve directamente **sus entidades**, sin agrupador de región.
- `administrador` / `super_admin`: ven las entidades **agrupadas por región**.

## Categorías

- Catálogo compartido y global (no por entidad).
- Cualquier usuario puede agregar una categoría nueva; queda disponible para todos.
- Para evitar duplicados, la comparación al crear **ignora mayúsculas y acentos**.
- Solo `super_admin` puede renombrar, fusionar o eliminar categorías.

## Generación del Reporte Focos Rojos

Flujo:

1. El usuario elige una entidad y pulsa **"Generar Reporte Focos Rojos"**.
2. Se abre un panel con los 4 datos iniciales del formato:
   - **Estado** — precargado con la entidad seleccionada.
   - **Fecha de entrega** — calendario, la define el usuario.
   - **Responsable que llena el reporte** — texto libre.
   - **Fecha de corte** — calendario, la define el usuario.
3. El usuario selecciona **cuáles** situaciones incluir, **hasta un máximo de 5**
   (el formato es "Top 5 focos rojos por estado"). Se sugieren por orden de importancia.
4. Vista previa del documento.
5. Si el resultado convence: botón **"Guardar versión en R2"**.

Salidas: `.docx` (rellenando la plantilla institucional) y `.pdf`.

## Versiones en Cloudflare R2

- Se guarda el archivo generado **más un JSON** con la foto de los datos de ese momento.
- Las versiones son **inmutables**: nadie las borra desde la aplicación.
- Visibilidad: `regional` ve solo las versiones de las entidades de su región;
  `administrador` y `super_admin` ven todas.

## Auditoría

- Quién creó y quién editó cada situación, y cuándo (bitácora, ver arriba).
- Quién generó cada reporte y cuándo.
- **Último acceso de cada usuario** — visible solo para `administrador` y `super_admin`.

## Identidad visual

Se reutiliza la estructura visual de `legacy/propuesta-02-modulo-ce-color.html`, pero con
**verde como color predominante y dorado como acento**, en lugar del guinda del mockup.
Los tokens ya existen en ese archivo: `--verde:#1E5B4F`, `--verde-d:#002F2A`,
`--verde-l:#2E8A77`, `--dorado:#A57F2C`, `--dorado-l:#D4AC4E`.

Interfaz en español. Los logos institucionales los proporcionará el usuario más adelante.


## Vista de concentrado (solo administradores)

Tabla de alcance nacional para cruzar datos entre estados: por ejemplo, ver todas las
prioridades 1 del país, o todo lo abierto en una categoría.

- **Filtros**: región, entidad, categoría, estatus, prioridad (1–5), búsqueda por tema
  o responsable, y alternador de archivadas.
- **Agrupación**: sin agrupar, por región, entidad, categoría, estatus o prioridad.
- Los regionales no la ven: para ellos sería su propia galería con más pasos.

## Identidad visual: marco de ventana

La aplicación se presenta **contenida dentro de un recuadro** con su propia barra de
título, no a sangre completa. Es una convención de diseño que el usuario usa en sus
aplicaciones y hay que conservarla. En pantallas menores a 860 px el marco desaparece
y la aplicación ocupa todo el ancho.
