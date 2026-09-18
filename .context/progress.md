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

### Fase 4 — Generación del reporte ✅
- [x] `reportes/plantilla.py`: mapa posicional y `escribir_celda` que hereda el `rPr`
- [x] `reportes/contexto.py`: concatenaciones solo al imprimir
- [x] `reportes/pdf.py`: LibreOffice con perfil aislado por invocación
- [x] `POST /api/reportes/vista-previa/` (PDF o .docx, sin persistir)
- [x] **Riesgo R2 resuelto**: PDF verificado visualmente contra el Word original
- [x] `.dockerignore`: el `.venv` se copiaba a la imagen (1.23 GB → 1.03 GB)

### Fase 3 — Frontend operativo ✅ compila; falta verlo en un navegador
- [x] Cliente axios con renovación de token y reintento único
- [x] `AuthContext` con recuperación de sesión al recargar
- [x] React Query + rutas protegidas por rol
- [x] Pantalla de acceso
- [x] Entidades: agrupadas por región para admins, lista plana para regionales
- [x] Galería con `@dnd-kit` (asa de arrastre en el número, accesible por teclado)
      y actualización optimista con reversión ante error
- [x] Formulario de situación con los 6 campos del formato
- [x] Selector de categoría con alta incorporada
- [x] Panel de detalle con bitácora en línea de tiempo
- [x] Asistente de reporte con vista previa en PDF embebido
- [x] Compilación de producción limpia: 155 módulos, 333 KB (108 KB gzip)

## Pendiente

### Verificación pendiente del frontend
- [ ] **Abrirlo en un navegador y recorrer el flujo completo.** La compilación pasa,
      pero no se ha visto renderizado: no hubo navegador disponible en la sesión.

### Fases 5–7
- [ ] Versiones en Cloudflare R2 (faltan credenciales del usuario)
- [ ] Administración y auditoría en el frontend
- [ ] Despliegue en Railway
- [ ] Nota de proyecto en la bóveda (`10 Projects/`)

## Cuentas en desarrollo

El entorno local necesita al menos un super administrador. Créalo así:

```bash
docker compose exec backend python manage.py createsuperuser
```

Después, desde la aplicación (Administración → Usuarios) se dan de alta las demás
cuentas. Para poblar las 24 entidades con situaciones de ejemplo:

```bash
docker compose exec backend python manage.py seed_ejemplos --limpiar
```

No se anotan contraseñas en el repositorio, ni siquiera de desarrollo.
