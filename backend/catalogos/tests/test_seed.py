"""El catalogo de regiones y entidades es fijo: 5 regiones, 24 entidades, cada
entidad en UNA sola region."""
import pytest
from django.core.management import call_command

from catalogos.models import Entidad, Region


@pytest.mark.django_db
def test_seed_crea_el_catalogo_completo():
    call_command("seed_catalogos")
    assert Region.objects.count() == 5
    assert Entidad.objects.count() == 24


@pytest.mark.django_db
def test_seed_es_idempotente():
    call_command("seed_catalogos")
    call_command("seed_catalogos")
    assert Region.objects.count() == 5
    assert Entidad.objects.count() == 24


@pytest.mark.django_db
def test_cada_entidad_pertenece_a_una_region():
    call_command("seed_catalogos")
    assert not Entidad.objects.filter(region__isnull=True).exists()
    conteos = {r.nombre: r.entidades.count() for r in Region.objects.all()}
    assert conteos == {
        "Centro": 3, "Noreste": 4, "Noroeste": 6, "Sureste": 6, "Suroeste": 5,
    }


@pytest.mark.django_db
def test_claves_sin_acentos():
    call_command("seed_catalogos")
    cdmx = Entidad.objects.get(nombre="Ciudad de México")
    assert cdmx.clave == "ciudad-de-mexico"
