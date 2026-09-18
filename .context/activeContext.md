# Active Context

> Última actualización: 2026-09-18

## En qué estamos

Fases 0, 1 y 2 terminadas y **verificadas contra PostgreSQL real** en Docker.
82 pruebas en verde (+12 omitidas). Prueba de humo de punta a punta con login JWT funcionando.

Siguiente paso: **Fase 3 (frontend operativo)** o **Fase 4 (generación del reporte)**.
La Fase 4 conviene pronto porque los riesgos R1 y R2 (tamaño de imagen y fidelidad
del PDF) siguen sin verificarse y condicionan el despliegue.

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| Stack | Django + DRF + PostgreSQL + React (Vite), Docker Compose, Railway |
| Autenticación | Propia (usuario/contraseña), no SSO |
| Cuentas | Solo las crea el `super_admin` |
| Regionales | Pertenecen a una sola región |
| Estatus | Enum (`ABIERTA`/`EN_PROCESO`/`CERRADA`) + comentario extenso |
| Cerradas | Se archivan, fuera de la galería por defecto |
| Bitácora | Por situación, visible para cualquiera que pueda ver esa situación |
| Reordenar | Cualquiera con acceso a la entidad; sin historial de reordenamientos |
| Reporte | Máximo 5 situaciones; `.docx` + `.pdf`; vista previa antes de guardar |
| Responsable | Texto libre, no usuario del sistema; separado de la fecha estimada |
| Versiones R2 | Inmutables, nadie las borra; archivo + JSON con la foto de los datos |
| Visibilidad de versiones | Regional solo las de su región; admins todas |
| Auditoría | Creación/edición de situaciones, generación de reportes, último acceso de usuarios |
| Último acceso | Visible solo para `administrador` y `super_admin` |
| Paleta | Verde predominante + dorado, tomados de los tokens del mockup |
| Vista por rol | Admins ven agrupado por región; regionales solo sus entidades |

## Pendientes de definir

- ~~Herramienta de conversión a PDF~~ → resuelto en el blueprint: LibreOffice headless + `fonts-noto-core` en la imagen del backend, aislado tras `reportes/pdf.py`.
- ~~Decisiones D1–D14~~ → cerradas con los valores por omisión del blueprint.
- Logos institucionales — el usuario los proporcionará después.

## Bloqueadores

- **Credenciales de Cloudflare R2**: sin ellas no se puede cerrar la Fase 5.
- **Logos institucionales**: pendientes de que el usuario los entregue.

## Hallazgos de la puesta en marcha

1. **Puertos reasignados.** En este equipo ya corrían `censo_db_container` (5432) y
   `contrataciones-backend-1` (8000). El proyecto publica **8001** (API) y **5436**
   (PostgreSQL). El frontend sigue en 5173.
2. **`ALLOWED_HOSTS` necesita `backend`.** El proxy de Vite reenvía con el Host del
   servicio de Docker, no `localhost`; sin eso, Django responde `DisallowedHost`.
3. **`docker compose restart` no relee el `env_file`.** Tras cambiar `.env` hay que usar
   `docker compose up -d --force-recreate <servicio>`.
4. **DRF y los `UniqueConstraint` condicionales no se llevan.** DRF autogeneraba un
   validador que exigía `archivada_en` (campo de solo lectura) y rompía cualquier PATCH
   con `KeyError`. Se desactivó con `validators = []` en el serializer; la garantía real
   la da la base de datos.
5. **La imagen pesa 1.23 GB**, no ~700 MB: esa cifra era solo el delta de LibreOffice.

## Cómo correr las pruebas sin Docker

```bash
cd backend
DATABASE_URL="sqlite://:memory:" ./.venv/Scripts/python.exe -m pytest
```

Ojo: SQLite sirve para el catálogo y el RBAC, pero la Fase 2 depende de un índice
único parcial de PostgreSQL. Ese comportamiento hay que verificarlo con Docker arriba.
