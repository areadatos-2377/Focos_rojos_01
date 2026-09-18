#!/bin/sh
set -e

echo "[entrypoint] Esperando a PostgreSQL..."
python - <<'PY'
import os, time, socket, urllib.parse
url = urllib.parse.urlparse(os.environ.get("DATABASE_URL", ""))
host, port = url.hostname or "db", url.port or 5432
for intento in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"[entrypoint] PostgreSQL disponible en {host}:{port}")
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit(f"[entrypoint] PostgreSQL no respondio en {host}:{port}")
PY

echo "[entrypoint] Aplicando migraciones..."
python manage.py migrate --noinput

echo "[entrypoint] Sembrando catalogos (regiones y entidades)..."
python manage.py seed_catalogos

if [ "$DJANGO_DEBUG" = "False" ]; then
  echo "[entrypoint] Recolectando estaticos..."
  python manage.py collectstatic --noinput
fi

exec "$@"
