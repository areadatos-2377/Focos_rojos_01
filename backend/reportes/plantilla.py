"""Rellenado del formato institucional .docx.

La plantilla NO tiene marcadores: sus celdas de valor estan vacias. El rellenado es
posicional, apoyado en que la estructura del documento es fija:

    Tabla 0      -> portada, 2 filas x 4 columnas
    Tablas 1..5  -> una por situacion, 6 filas x 2 columnas (etiqueta | valor)

`test_plantilla.py` verifica esa estructura: si alguien sustituye el .docx por otro,
la suite falla de inmediato en vez de producir reportes en blanco en produccion.
"""
import copy
from pathlib import Path

from django.conf import settings
from docx import Document
from docx.oxml.ns import qn

RUTA_PLANTILLA = Path(settings.BASE_DIR) / "reportes" / "plantillas" / "formato_focos_rojos.docx"

#: Maximo de situaciones por reporte. El formato es "Top 5 focos rojos por estado".
MAX_SITUACIONES = 5

#: Portada: campo -> (indice de fila, indice de celda) dentro de la tabla 0.
CELDAS_PORTADA = {
    "estado": (0, 1),
    "fecha_entrega": (0, 3),
    "responsable_reporte": (1, 1),
    "fecha_corte": (1, 3),
}

#: Situacion: el valor va siempre en la celda 1; el indice de la lista es la fila.
FILAS_SITUACION = [
    "categoria",
    "tema",
    "fecha_inicio",
    "estatus_actual",
    "acciones",
    "responsable_fecha",
]

#: Etiquetas esperadas en la columna 0, para detectar una plantilla cambiada.
ETIQUETAS_PORTADA = {
    (0, 0): "Estado",
    (0, 2): "Fecha de entrega",
    (1, 0): "Responsable que llena el reporte",
    (1, 2): "Fecha de corte",
}
ETIQUETAS_SITUACION = [
    "Categoría",
    "Tema",
    "Fecha de inicio",
    "Estatus actual",
    "Acciones que se están realizando",
    "Responsable / Fecha estimada",
]

#: Elementos de formato que no se heredan al texto (marcas de control de cambios).
_NO_HEREDABLES = {
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ins",
    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}del",
}


def _heredar_formato(parrafo, run) -> None:
    """Copia al run el formato de caracter que la plantilla dejo en el parrafo.

    Las celdas vacias traen un `w:rPr` dentro del `w:pPr` que apunta a Noto Sans.
    Si no se copia, el texto sale con la fuente por defecto y descuadra la tabla.
    """
    pPr = parrafo._p.pPr
    if pPr is None:
        return
    # `CT_PPr` no expone `.rPr` como atributo: hay que buscar el elemento.
    rPr_origen = pPr.find(qn("w:rPr"))
    if rPr_origen is None:
        return
    rPr_destino = run._r.get_or_add_rPr()
    for hijo in rPr_origen:
        if hijo.tag in _NO_HEREDABLES:
            continue
        rPr_destino.append(copy.deepcopy(hijo))


def escribir_celda(celda, texto) -> None:
    """Escribe en una celda conservando su formato.

    No se usa `celda.text = ...`: esa via reemplaza el parrafo entero y se lleva por
    delante el `pPr`/`rPr` de la plantilla (fuente, tamano, espaciado).

    Los saltos de linea se insertan como `w:br` dentro del mismo run, en vez de crear
    parrafos nuevos, para no alterar la altura de la fila.
    """
    parrafo = celda.paragraphs[0]

    for run in list(parrafo.runs):
        run._r.getparent().remove(run._r)
    for sobrante in celda.paragraphs[1:]:
        sobrante._p.getparent().remove(sobrante._p)

    if texto is None:
        return
    texto = str(texto)
    if not texto:
        return

    lineas = texto.split("\n")
    run = parrafo.add_run(lineas[0])
    _heredar_formato(parrafo, run)
    for linea in lineas[1:]:
        run.add_break()
        run.add_text(linea)


def abrir_plantilla() -> Document:
    """Abre una copia en memoria. El archivo en disco nunca se modifica."""
    return Document(str(RUTA_PLANTILLA))


def rellenar(contexto: dict) -> Document:
    """Devuelve el documento ya rellenado.

    `contexto` es lo que produce `reportes.contexto.construir_contexto`:
    un bloque `portada` y una lista `situaciones` de a lo mas 5 elementos, cada uno
    con las claves de `FILAS_SITUACION`.

    Los bloques de situacion sobrantes se dejan en blanco: el formato es fijo de 5.
    """
    documento = abrir_plantilla()

    portada = documento.tables[0]
    for campo, (fila, celda) in CELDAS_PORTADA.items():
        escribir_celda(portada.rows[fila].cells[celda], contexto["portada"].get(campo, ""))

    situaciones = contexto["situaciones"][:MAX_SITUACIONES]
    for indice, datos in enumerate(situaciones):
        tabla = documento.tables[1 + indice]
        for fila, campo in enumerate(FILAS_SITUACION):
            escribir_celda(tabla.rows[fila].cells[1], datos.get(campo, ""))

    return documento
