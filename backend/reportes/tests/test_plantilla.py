"""Blindaje de la plantilla institucional.

El rellenado es posicional: depende de que la tabla 0 sea la portada y las tablas
1..5 los bloques de situacion. Si alguien sustituye el .docx por una version con
otra estructura, estas pruebas fallan de inmediato, en vez de generar reportes en
blanco sin que nadie lo note.
"""
import pytest

from reportes import plantilla


def test_la_plantilla_existe():
    assert plantilla.RUTA_PLANTILLA.exists(), (
        f"Falta la plantilla en {plantilla.RUTA_PLANTILLA}. Sin ella no se puede "
        "generar ningun reporte."
    )


def test_la_estructura_es_la_esperada():
    documento = plantilla.abrir_plantilla()

    assert len(documento.tables) == 6, "Se esperan 6 tablas: portada + 5 situaciones."

    portada = documento.tables[0]
    assert (len(portada.rows), len(portada.columns)) == (2, 4)

    for indice in range(1, 6):
        tabla = documento.tables[indice]
        assert (len(tabla.rows), len(tabla.columns)) == (6, 2), (
            f"La tabla {indice} deberia ser 6x2 (etiqueta | valor)."
        )


def test_las_etiquetas_de_la_portada_no_cambiaron():
    portada = plantilla.abrir_plantilla().tables[0]
    for (fila, celda), esperado in plantilla.ETIQUETAS_PORTADA.items():
        real = portada.rows[fila].cells[celda].text.strip()
        assert real.startswith(esperado), (
            f"La celda ({fila},{celda}) deberia decir '{esperado}' y dice '{real}'."
        )


def test_las_etiquetas_de_situacion_no_cambiaron():
    documento = plantilla.abrir_plantilla()
    for indice in range(1, 6):
        tabla = documento.tables[indice]
        for fila, esperado in enumerate(plantilla.ETIQUETAS_SITUACION):
            real = tabla.rows[fila].cells[0].text.strip()
            assert real.startswith(esperado), (
                f"Tabla {indice}, fila {fila}: se esperaba '{esperado}' y hay '{real}'."
            )


def test_las_celdas_de_valor_llegan_vacias():
    """Si vinieran con texto, el rellenado lo estaria pisando sin avisar."""
    documento = plantilla.abrir_plantilla()
    for indice in range(1, 6):
        for fila in documento.tables[indice].rows:
            assert fila.cells[1].text.strip() == ""


@pytest.fixture
def contexto_de_prueba():
    return {
        "portada": {
            "estado": "Chiapas",
            "fecha_entrega": "16/08/2026",
            "responsable_reporte": "Dr. Juan Ramirez",
            "fecha_corte": "14/08/2026",
        },
        "situaciones": [
            {
                "categoria": "Infraestructura",
                "tema": "Desabasto de medicamentos",
                "fecha_inicio": "02/05/2026",
                "estatus_actual": "En proceso — Surtido parcial.",
                "acciones": "Primera linea.\nSegunda linea.",
                "responsable_fecha": "Ing. Perez / 30/09/2026",
            },
            {
                "categoria": "Logística",
                "tema": "Falta de transporte",
                "fecha_inicio": "10/06/2026",
                "estatus_actual": "Abierta",
                "acciones": "Se solicito apoyo.",
                "responsable_fecha": "Lic. Gomez",
            },
        ],
    }


def test_rellenar_escribe_la_portada(contexto_de_prueba):
    documento = plantilla.rellenar(contexto_de_prueba)
    portada = documento.tables[0]

    assert portada.rows[0].cells[1].text == "Chiapas"
    assert portada.rows[0].cells[3].text == "16/08/2026"
    assert portada.rows[1].cells[1].text == "Dr. Juan Ramirez"
    assert portada.rows[1].cells[3].text == "14/08/2026"


def test_rellenar_escribe_cada_situacion_en_su_bloque(contexto_de_prueba):
    documento = plantilla.rellenar(contexto_de_prueba)

    primera = documento.tables[1]
    assert primera.rows[0].cells[1].text == "Infraestructura"
    assert primera.rows[1].cells[1].text == "Desabasto de medicamentos"
    assert primera.rows[5].cells[1].text == "Ing. Perez / 30/09/2026"

    segunda = documento.tables[2]
    assert segunda.rows[1].cells[1].text == "Falta de transporte"


def test_los_bloques_sobrantes_quedan_en_blanco(contexto_de_prueba):
    """Decision D5: el formato es fijo de 5; lo que sobra se deja vacio."""
    documento = plantilla.rellenar(contexto_de_prueba)

    for indice in (3, 4, 5):
        for fila in documento.tables[indice].rows:
            assert fila.cells[1].text.strip() == ""


def test_se_respeta_el_maximo_de_cinco(contexto_de_prueba):
    contexto_de_prueba["situaciones"] = [
        dict(contexto_de_prueba["situaciones"][0], tema=f"Situacion {i}")
        for i in range(1, 9)
    ]
    documento = plantilla.rellenar(contexto_de_prueba)

    assert documento.tables[5].rows[1].cells[1].text == "Situacion 5"
    assert len(documento.tables) == 6  # no se agregan tablas nuevas


def test_los_saltos_de_linea_no_crean_parrafos(contexto_de_prueba):
    """Se insertan como w:br dentro del mismo run: un parrafo extra alteraria la
    altura de la fila y descuadraria el formato."""
    documento = plantilla.rellenar(contexto_de_prueba)
    celda = documento.tables[1].rows[4].cells[1]

    assert len(celda.paragraphs) == 1
    assert "Primera linea." in celda.text
    assert "Segunda linea." in celda.text


def test_se_conserva_el_formato_de_la_plantilla(contexto_de_prueba):
    """El texto debe heredar la fuente que la plantilla dejo en el parrafo vacio."""
    documento = plantilla.rellenar(contexto_de_prueba)
    run = documento.tables[1].rows[1].cells[1].paragraphs[0].runs[0]

    assert run._r.rPr is not None, (
        "El run salio sin formato: se perdio el rPr de la plantilla y el texto "
        "usara la fuente por defecto."
    )


def test_el_archivo_original_no_se_toca(contexto_de_prueba):
    antes = plantilla.RUTA_PLANTILLA.read_bytes()
    plantilla.rellenar(contexto_de_prueba)
    assert plantilla.RUTA_PLANTILLA.read_bytes() == antes
