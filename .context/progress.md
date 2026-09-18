# Progress

## Completado

- [x] Levantamiento de requisitos con el usuario
- [x] Blueprint técnico aprobado → `docs/planes_de_cambios/001-blueprint-inicial.md`

### Fase 0 — Andamiaje ✅ verificado con `docker compose up`
- [x] `git init`, `.gitignore`, `.gitattributes` (LF forzado), `README.md`, `CLAUDE.md`, `.env`
- [x] Proyecto Django `config` (settings 12-factor, DRF, JWT, CORS, WhiteNoise)
- [x] `Dockerfile` con LibreOffice + `fonts-noto-core` — **imagen de 1.23 GB**
- [x] `entrypoint.sh` (espera a PostgreSQL → migrate → seed)
- [x] `docker-compose.yml` — **puertos 8001 y 5436** (8000 y 5432 ya ocupados en este equipo)
- [x] Vite + React con `tokens.css` verde/dorado y pantalla de estado

### Fase 1 — Identidad, catálogos y RBAC ✅
- [x] `usuarios.Usuario` como `AUTH_USER_MODEL` desde la primera migración (riesgo R4 eliminado)
- [x] `usuarios.RegistroAcceso` + `ultimo_acceso`
- [x] `catalogos`: `Region`, `Entidad`, `Categoria` + normalización + seed idempotente
- [x] **`core/`: punto único de RBAC** (`scoping`, `mixins`, `fields`, `permissions`)
- [x] JWT: login, refresh, logout, `yo`, cambiar contraseña
- [x] Gestión de usuarios (solo super_admin) y auditoría de accesos (solo admins)
- [x] **Meta-test del router** — comprobado que sí detecta un viewset sin el mixin

### Fase 2 — Situaciones y bitácora ✅
- [x] `Situacion` y `BitacoraSituacion` con constraints e índice único parcial
- [x] `situaciones/services.py`: orden denso, cierre con densificación, reapertura,
      reordenamiento en dos fases (`+10000`)
- [x] Bitácora campo a campo, con valores renderizados a texto estable
- [x] API completa + filtros + `PUT /entidades/{clave}/orden-situaciones/`

### Verificación
- [x] **82 pruebas en verde sobre PostgreSQL real** (+12 omitidas: parametrizaciones del
      meta-test que no aplican). `docker compose exec backend pytest`
- [x] Prueba de humo de punta a punta con login JWT real: alcance por región,
      categoría idempotente, alta, reordenamiento, 409 ante lista parcial, cierre con
      densificación, archivadas y bitácora

## Pendiente

### Fase 3 — Frontend operativo
- [ ] Cliente axios + React Query + `AuthContext` + rutas protegidas
- [ ] Pantalla de entidades (agrupada por región para admins)
- [ ] Galería con `@dnd-kit` y actualización optimista
- [ ] Formulario de situación, selector de categoría creatable, panel de bitácora

### Fase 4 — Reporte  ⚠️ los riesgos R1 y R2 siguen sin verificarse
- [ ] `reportes/plantilla.py` (mapa posicional + `escribir_celda`) y test de estructura
- [ ] `reportes/pdf.py` con LibreOffice y perfil aislado
- [ ] **Comparar visualmente el PDF generado contra el Word original** (paso 20)
- [ ] Vista previa

### Fases 5–7
- [ ] Versiones en Cloudflare R2 (faltan credenciales del usuario)
- [ ] Administración y auditoría en el frontend
- [ ] Despliegue en Railway
- [ ] Nota de proyecto en la bóveda (`10 Projects/`)

## Datos de acceso en desarrollo

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `FocosRojos2026!` | super_admin |
| `ana` | `FocosRojos2026!` | regional (Sureste) |

Solo para el entorno local. Hay datos de prueba en Chiapas.
