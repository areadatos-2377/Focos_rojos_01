"""Conversion de .docx a PDF con LibreOffice headless.

Toda la dependencia de LibreOffice esta contenida en `docx_a_pdf`. Si mas adelante
hay que mover la conversion a un servicio aparte (Gotenberg, por el peso de la
imagen), se reemplaza esta unica funcion y nada mas del proyecto se entera.
"""
import logging
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

#: Margen amplio: el primer arranque de LibreOffice tarda unos segundos.
TIEMPO_LIMITE = 90


class ErrorConversionPDF(RuntimeError):
    """LibreOffice no pudo producir el PDF."""


def libreoffice_disponible() -> bool:
    return shutil.which("soffice") is not None


def docx_a_pdf(contenido_docx: bytes) -> bytes:
    """Convierte un .docx en memoria a PDF y devuelve los bytes.

    Cada invocacion usa un perfil de usuario propio (`-env:UserInstallation`). Sin
    eso, dos peticiones simultaneas chocan por el mismo perfil y LibreOffice se
    cuelga o falla: es el modo tipico en que esto se rompe bajo varios workers.
    """
    if not libreoffice_disponible():
        raise ErrorConversionPDF(
            "LibreOffice no esta instalado en este entorno. La generacion de PDF "
            "requiere el contenedor del backend (soffice)."
        )

    with tempfile.TemporaryDirectory(prefix="reporte_") as carpeta:
        carpeta = Path(carpeta)
        origen = carpeta / "reporte.docx"
        origen.write_bytes(contenido_docx)

        perfil = carpeta / f"perfil_{uuid.uuid4().hex}"

        try:
            proceso = subprocess.run(
                [
                    "soffice",
                    "--headless",
                    "--norestore",
                    f"-env:UserInstallation=file://{perfil}",
                    "--convert-to",
                    "pdf:writer_pdf_Export",
                    "--outdir",
                    str(carpeta),
                    str(origen),
                ],
                capture_output=True,
                timeout=TIEMPO_LIMITE,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise ErrorConversionPDF(
                f"La conversion a PDF excedio {TIEMPO_LIMITE} segundos."
            ) from error

        destino = carpeta / "reporte.pdf"
        if proceso.returncode != 0 or not destino.exists():
            logger.error(
                "Fallo la conversion a PDF (codigo %s): %s",
                proceso.returncode,
                proceso.stderr.decode("utf-8", "replace")[:500],
            )
            raise ErrorConversionPDF(
                "LibreOffice no genero el PDF. Revisa los logs del backend."
            )

        return destino.read_bytes()


def documento_a_bytes(documento) -> bytes:
    """Serializa un `docx.Document` a bytes sin pasar por disco."""
    import io

    memoria = io.BytesIO()
    documento.save(memoria)
    return memoria.getvalue()
