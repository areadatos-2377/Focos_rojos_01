"""La normalizacion es lo unico que impide categorias duplicadas. Si cambia, se rompe
la unicidad del catalogo, asi que su comportamiento queda fijado aqui."""
import pytest

from catalogos.normalizacion import normalizar_nombre


@pytest.mark.parametrize(
    "entrada",
    ["Logística", "logística", "LOGÍSTICA", "Logistica", "  Logística  "],
)
def test_variantes_de_logistica_colapsan_al_mismo_valor(entrada):
    assert normalizar_nombre(entrada) == "logistica"


def test_espacios_internos_se_colapsan():
    assert normalizar_nombre("Recursos    Humanos") == "recursos humanos"


def test_distintas_categorias_no_colisionan():
    assert normalizar_nombre("Seguridad") != normalizar_nombre("Seguridad Vial")


def test_cadena_vacia():
    assert normalizar_nombre("") == ""
    assert normalizar_nombre("   ") == ""


def test_acentos_de_todo_tipo():
    assert normalizar_nombre("Comunicación") == "comunicacion"
    assert normalizar_nombre("Infraestructura Básica") == "infraestructura basica"
