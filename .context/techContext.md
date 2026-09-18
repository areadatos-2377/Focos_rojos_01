# Tech Context — Reporte Focos Rojos

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Django + Django REST Framework |
| Base de datos | PostgreSQL (contenedor en desarrollo) |
| Frontend | React + Vite |
| Autenticación | Propia, usuario/contraseña, sesión vía JWT |
| Contenedores | Docker + Docker Compose |
| Almacenamiento de versiones | Cloudflare R2 (API S3, vía `boto3`) |
| Despliegue | Railway |
| Servidor WSGI | Gunicorn |

## Generación de documentos

- `.docx`: se rellena la plantilla institucional
  `legacy/Formato_Focos_Rojos_Gira_INSTITUCIONAL.docx` (estructura: 4 datos iniciales +
  5 bloques "SITUACIÓN N" con 6 campos cada uno).
- `.pdf`: conversión a partir del `.docx` generado. La herramienta concreta
  (LibreOffice headless u otra) queda a definir en el plan de implementación — condiciona
  la imagen Docker del backend.

## Convenciones heredadas del proyecto anterior

De `30 Resources/Patron - Worker Timeout por IO Externo Lento sin Limite`:

1. **Nunca crear un cliente boto3 sin timeout explícito.**
   `Config(connect_timeout=10, read_timeout=20, retries={"max_attempts": 2})`.
2. **Sacar el trabajo largo del ciclo request/response** si llega a tardar. Para el volumen
   de este proyecto (máximo 5 situaciones por reporte, ~20 usuarios) la generación es
   síncrona; **no** se necesita Celery ni jobs en hilo. Si eso cambia, el patrón a seguir es
   `threading.Thread` + modelo `Job` con estado en base de datos y polling desde el frontend.
3. Un cliente `boto3` (no un `Resource`) sí es seguro compartir entre hilos.

## Variables de entorno

Pendiente de definir en el plan. Como mínimo:

```
DATABASE_URL
DJANGO_SECRET_KEY
DJANGO_DEBUG
R2_ACCOUNT_ID
R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY
R2_BUCKET_NAME
R2_ENDPOINT_URL
```

Nunca versionar credenciales: `.env` fuera de git, `.env.example` como plantilla.

## Entorno de desarrollo

Docker Compose levanta backend, frontend y PostgreSQL. El mismo Compose es la base del
despliegue en Railway.

Plataforma de desarrollo: Windows 11, PowerShell.
