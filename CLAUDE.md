# Convenciones — Reporte Focos Rojos

## Antes de empezar una sesión

1. Lee `.context/activeContext.md` (dónde se quedó) y `.context/progress.md` (qué falta).
2. El blueprint vigente está en `docs/planes_de_cambios/`. Es la fuente de verdad de
   qué se está construyendo.
3. Al cerrar la sesión, actualiza `activeContext.md` y `progress.md`.

## Reglas que no se negocian

- **`legacy/` es inmutable.** El `.docx` institucional no se edita nunca; se lee y se
  rellena una copia. Su estructura es posicional (tabla 0 = portada 2×4;
  tablas 1–5 = situaciones 6×2) y hay un test que lo verifica.
- **El RBAC por región vive solo en `core/scoping.py`.** Ninguna vista reimplementa la
  regla: los ViewSets heredan `AlcanceEntidadMixin` y los serializers usan
  `EntidadPermitidaField`. Un objeto fuera de alcance devuelve 404, no 403.
- **El orden de las situaciones es un entero denso 1..N entre las activas de cada
  entidad.** Nunca actualices `orden` con un `bulk_update` directo: el índice único
  parcial de PostgreSQL no admite `DEFERRABLE`, así que hay que desplazar `+10000`
  primero. Toda esa lógica vive en `situaciones/services.py`.
- **Los reportes guardados en R2 son inmutables.** No hay `update` ni `destroy` en su
  ViewSet, y el token de R2 se emite sin permiso de borrado.
- **Nunca crear un cliente boto3 sin timeouts explícitos**
  (`connect_timeout=10`, `read_timeout=20`).
- **`AUTH_USER_MODEL` ya está fijado.** Cambiarlo obliga a recrear la base entera.

## Estilo

- Nombres de modelos, campos y rutas **en español**. Interfaz en español, incluidos
  los mensajes de error de la API.
- La lógica no trivial va en el `services.py` de su app, no en las vistas ni en `save()`.
- Paleta: verde primario (`--verde: #1E5B4F`), dorado de acento (`--dorado: #A57F2C`).
  El guinda queda reservado para alertas, no para la identidad.
