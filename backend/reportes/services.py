"""Generacion del Reporte Focos Rojos.

`generar_documentos` es el unico camino que produce un reporte. La vista previa y el
guardado definitivo lo usan igual, para que lo que el usuario ve sea exactamente lo
que se guarda: una sola implementacion, sin una segunda que se desincronice.
"""
import datetime as dt

from situaciones.models import Situacion

from .contexto import construir_contexto
from .pdf import docx_a_pdf, documento_a_bytes
from .plantilla import MAX_SITUACIONES, rellenar


class SeleccionInvalida(ValueError):
    """Las situaciones elegidas no sirven para este reporte."""


def resolver_situaciones(entidad, ids: list[int]) -> list[Situacion]:
    """Valida la seleccion y la devuelve EN EL ORDEN PEDIDO.

    El orden de la lista es el que determina cual es SITUACION 1, 2, 3...  No se usa
    el orden de importancia guardado: al generar el reporte el usuario puede querer
    un orden distinto para esa entrega puntual.
    """
    if not ids:
        raise SeleccionInvalida("Elige al menos una situacion para el reporte.")
    if len(ids) > MAX_SITUACIONES:
        raise SeleccionInvalida(
            f"El formato admite un maximo de {MAX_SITUACIONES} situaciones "
            f"(se recibieron {len(ids)})."
        )
    if len(set(ids)) != len(ids):
        raise SeleccionInvalida("Hay situaciones repetidas en la seleccion.")

    encontradas = {
        s.pk: s
        for s in Situacion.objects.select_related("categoria", "entidad")
        .filter(pk__in=ids, entidad=entidad)
        .activas()
    }

    faltantes = [i for i in ids if i not in encontradas]
    if faltantes:
        raise SeleccionInvalida(
            "Algunas situaciones no existen, no son de esta entidad o ya estan "
            "archivadas. Recarga la vista e intenta de nuevo."
        )

    return [encontradas[i] for i in ids]


def generar_documentos(
    *,
    entidad,
    situaciones: list[Situacion],
    fecha_entrega: dt.date,
    responsable_reporte: str,
    fecha_corte: dt.date,
) -> tuple[bytes, bytes, dict]:
    """Devuelve (docx, pdf, contexto). El contexto alimenta el snapshot de R2."""
    contexto = construir_contexto(
        entidad=entidad,
        situaciones=situaciones,
        fecha_entrega=fecha_entrega,
        responsable_reporte=responsable_reporte,
        fecha_corte=fecha_corte,
    )
    documento = rellenar(contexto)
    contenido_docx = documento_a_bytes(documento)
    contenido_pdf = docx_a_pdf(contenido_docx)
    return contenido_docx, contenido_pdf, contexto


def nombre_archivo(entidad, fecha_corte: dt.date, version: int | None = None) -> str:
    """Nombre amigable para la descarga (no es la llave de R2)."""
    sufijo = f"_v{version}" if version else ""
    return f"focos-rojos_{entidad.clave}_{fecha_corte:%Y-%m-%d}{sufijo}"
