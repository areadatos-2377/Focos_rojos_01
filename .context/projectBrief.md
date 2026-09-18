# Project Brief — Reporte Focos Rojos

## Objetivo

Aplicación web para registrar y dar seguimiento a las **situaciones** problemáticas de cada
entidad federativa (focos rojos), y generar a partir de ellas el **Reporte Focos Rojos** en
el formato institucional preestablecido (`legacy/Formato_Focos_Rojos_Gira_INSTITUCIONAL.docx`).

Hoy ese reporte se llena a mano en Word, estado por estado. La aplicación centraliza el
registro, conserva el histórico y automatiza la generación del documento.

## Usuarios objetivo

~20 usuarios, en tres roles:

| Rol | Alcance | Puede |
|---|---|---|
| `regional` | Solo las entidades de **su** región (pertenece a una sola) | Ver, registrar, editar, reordenar y generar reportes de sus entidades |
| `administrador` | Todas las entidades, agrupadas por región | Lo mismo que regional, en todo el país |
| `super_admin` | Todas las entidades | Además: gestión de usuarios y de catálogos (categorías) |

## Alcance (v1)

- Registro de situaciones con el formato de 6 propiedades del documento institucional.
- Galería de situaciones por entidad, con orden de importancia arrastrable (1 = más urgente).
- Catálogo de categorías compartido y ampliable por cualquier usuario.
- Generación del Reporte Focos Rojos (hasta 5 situaciones) en `.docx` y `.pdf`, con vista previa.
- Guardado de versiones del reporte en Cloudflare R2, inmutables.
- Bitácora de cambios por situación y registro de accesos de usuarios.

## Fuera de alcance (v1)

- Notificaciones por correo o recordatorios automáticos.
- SSO institucional (se usa autenticación propia usuario/contraseña).
- App móvil nativa.

## Referencias

- Formato fuente: `legacy/Formato_Focos_Rojos_Gira_INSTITUCIONAL.docx`
- Referencia visual: `legacy/propuesta-02-modulo-ce-color.html`
- Catálogo de regiones: bóveda Obsidian, `30 Resources/Ref - Regiones Operativas IMSS-Bienestar.md`
- Protocolo de trabajo: bóveda Obsidian, `30 Resources/Protocolo Multi-Agentes - Claude Code.md`
