"""El aislamiento por region es la garantia central del sistema: un regional no debe
poder ver ni tocar entidades de otra region. Si estas pruebas fallan, hay una fuga."""
import pytest

from core.scoping import entidades_visibles


@pytest.mark.django_db
def test_regional_solo_ve_las_entidades_de_su_region(regional_sureste):
    visibles = entidades_visibles(regional_sureste)
    assert visibles.count() == 6
    assert set(visibles.values_list("nombre", flat=True)) == {
        "Campeche", "Chiapas", "Oaxaca", "Quintana Roo", "Tabasco", "Yucatán",
    }


@pytest.mark.django_db
def test_dos_regionales_distintos_no_comparten_entidades(regional_sureste, regional_centro):
    sureste = set(entidades_visibles(regional_sureste).values_list("pk", flat=True))
    centro = set(entidades_visibles(regional_centro).values_list("pk", flat=True))
    assert sureste.isdisjoint(centro)


@pytest.mark.django_db
def test_administrador_ve_todas_las_entidades(administrador):
    assert entidades_visibles(administrador).count() == 24


@pytest.mark.django_db
def test_api_entidades_respeta_el_alcance(cliente, regional_sureste, administrador):
    respuesta = cliente(regional_sureste).get("/api/entidades/")
    assert respuesta.status_code == 200
    assert len(respuesta.data) == 6

    respuesta_admin = cliente(administrador).get("/api/entidades/")
    assert len(respuesta_admin.data) == 24


@pytest.mark.django_db
def test_entidad_de_otra_region_responde_404_no_403(cliente, regional_sureste):
    """404 y no 403: no se revela que la entidad exista."""
    respuesta = cliente(regional_sureste).get("/api/entidades/hidalgo/")
    assert respuesta.status_code == 404

    propia = cliente(regional_sureste).get("/api/entidades/chiapas/")
    assert propia.status_code == 200


@pytest.mark.django_db
def test_regional_solo_ve_su_region_en_el_listado_de_regiones(cliente, regional_sureste):
    respuesta = cliente(regional_sureste).get("/api/regiones/")
    assert [r["clave"] for r in respuesta.data] == ["sureste"]


@pytest.mark.django_db
def test_sin_autenticar_no_se_ve_nada(cliente):
    assert cliente().get("/api/entidades/").status_code == 401
