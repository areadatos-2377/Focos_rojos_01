"""Traduce los datos del sistema al texto que se imprime en cada celda del formato.

Es la unica pieza que decide como se ve el reporte. Vive aparte del rellenado para
que el snapshot que se guarda en R2 pueda registrar exactamente el mismo texto que
se imprimio, sin depender de la logica de renderizado vigente en el futuro.
"""
import datetime as dt

from situaciones.models import Estatus, Situacion

FORMATO_FECHA = "%d/%m/%Y"


def fecha_larga(valor: dt.date | None) -> str:
    return valor.strftime(FORMATO_FECHA) if valor else ""


def texto_estatus(situacion: Situacion) -> str:
    """Decision D7: la celda lleva la etiqueta del estatus y luego el detalle.

    Asi el Word muestra de un vistazo si esta abierta o en proceso, algo que el
    formato original no distinguia.
    """
    etiqueta = Estatus(situacion.estatus).label
    detalle = (situacion.estatus_detalle or "").strip()
    return f"{etiqueta} — {detalle}" if detalle else etiqueta


def texto_responsable_fecha(situacion: Situacion) -> str:
    """En el formato son una sola celda; en el sistema son dos campos.

    Decision D1: la fecha estimada es opcional. Si falta, se imprime solo el
    responsable en vez de dejar una barra suelta.
    """
    responsable = (situacion.responsable or "").strip()
    fecha = fecha_larga(situacion.fecha_estimada_solucion)
    if responsable and fecha:
        return f"{responsable} / {fecha}"
    return responsable or fecha


def situacion_a_celdas(situacion: Situacion) -> dict:
    """Las 6 celdas de un bloque SITUACION."""
    return {
        "categoria": situacion.categoria.nombre,
        "tema": situacion.tema,
        "fecha_inicio": fecha_larga(situacion.fecha_inicio),
        "estatus_actual": texto_estatus(situacion),
        "acciones": situacion.acciones,
        "responsable_fecha": texto_responsable_fecha(situacion),
    }


def construir_contexto(
    *,
    entidad,
    situaciones,
    fecha_entrega: dt.date,
    responsable_reporte: str,
    fecha_corte: dt.date,
) -> dict:
    """Arma el contexto completo del reporte.

    `situaciones` llega ya ordenada y filtrada por quien genera el reporte: el orden
    de la lista es el que aparece como SITUACION 1..5 en el documento.
    """
    return {
        "portada": {
            "estado": entidad.nombre,
            "fecha_entrega": fecha_larga(fecha_entrega),
            "responsable_reporte": responsable_reporte,
            "fecha_corte": fecha_larga(fecha_corte),
        },
        "situaciones": [situacion_a_celdas(s) for s in situaciones],
    }
