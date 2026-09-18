# Reporte Focos Rojos

Aplicación web para registrar y dar seguimiento a las **situaciones** problemáticas
(focos rojos) de cada entidad federativa, y generar a partir de ellas el
**Reporte Focos Rojos** en el formato institucional.

## Puesta en marcha

Requisitos: Docker y Docker Compose.

```bash
cp .env.example .env     # ajusta credenciales de R2 cuando las tengas
docker compose up --build
```

La primera construcción tarda varios minutos: la imagen del backend instala
LibreOffice, que es lo que convierte el `.docx` generado a PDF conservando el
membrete institucional.

| Servicio | URL |
|---|---|
| Frontend (Vite) | http://localhost:5173 |
| API | http://localhost:8001/api/ |
| Admin de Django | http://localhost:8001/admin/ |
| Sonda de salud | http://localhost:8001/api/salud/ |

> Los puertos publicados son 8001 y 5436 (no los habituales 8000 y 5432) porque en
> este equipo ya los ocupan otros proyectos.

Al arrancar, el contenedor aplica migraciones y siembra el catálogo de
**5 regiones operativas y 24 entidades**.

Para crear el primer super administrador:

```bash
docker compose exec backend python manage.py createsuperuser
```

## Estructura

```
backend/     Django + DRF
  config/      settings, urls, wsgi
  core/        RBAC por región (punto único), paginación, cliente R2
  usuarios/    Usuario (AUTH_USER_MODEL), JWT, registro de accesos
  catalogos/   Región, Entidad, Categoría + seed
  situaciones/ Situación, bitácora, orden de importancia
  reportes/    Generación .docx/.pdf y versiones en Cloudflare R2
frontend/    React + Vite
legacy/      Formato institucional original — NO se modifica
docs/        Blueprints de cambios
.context/    Memoria persistente entre sesiones
```

## Documentación

- **Qué se está construyendo:** [`docs/planes_de_cambios/001-blueprint-inicial.md`](docs/planes_de_cambios/001-blueprint-inicial.md)
- **Reglas de negocio:** [`.context/productContext.md`](.context/productContext.md)
- **Estado actual y decisiones:** [`.context/activeContext.md`](.context/activeContext.md)

## Pruebas

```bash
docker compose exec backend pytest
```
