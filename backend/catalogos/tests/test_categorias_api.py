"""El catalogo de categorias es compartido y cualquiera puede ampliarlo. La regla
que lo sostiene: dar de alta una categoria que ya existe (aunque este escrita con
otras mayusculas o acentos) devuelve la existente, no crea un duplicado ni falla."""
import pytest

from catalogos.models import Categoria
from usuarios.models import Rol


@pytest.mark.django_db
def test_crear_categoria_nueva_devuelve_201(cliente, regional_sureste):
    respuesta = cliente(regional_sureste).post(
        "/api/categorias/", {"nombre": "Infraestructura"}, format="json"
    )
    assert respuesta.status_code == 201
    assert Categoria.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("variante", ["LOGÍSTICA", "logística", "Logistica", " Logística "])
def test_categoria_existente_devuelve_200_y_no_duplica(cliente, regional_sureste, variante):
    c = cliente(regional_sureste)
    c.post("/api/categorias/", {"nombre": "Logística"}, format="json")

    respuesta = c.post("/api/categorias/", {"nombre": variante}, format="json")
    assert respuesta.status_code == 200
    assert Categoria.objects.count() == 1
    # Se conserva el nombre con que se creo originalmente.
    assert respuesta.data["nombre"] == "Logística"


@pytest.mark.django_db
def test_dos_regionales_distintos_comparten_el_catalogo(
    cliente, regional_sureste, regional_centro
):
    cliente(regional_sureste).post(
        "/api/categorias/", {"nombre": "Seguridad"}, format="json"
    )
    respuesta = cliente(regional_centro).get("/api/categorias/")
    assert [c["nombre"] for c in respuesta.data] == ["Seguridad"]


@pytest.mark.django_db
def test_nombre_demasiado_corto_se_rechaza(cliente, regional_sureste):
    respuesta = cliente(regional_sureste).post(
        "/api/categorias/", {"nombre": "RH"}, format="json"
    )
    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_regional_no_puede_renombrar_categorias(cliente, regional_sureste):
    categoria = Categoria.objects.create(nombre="Comunicación")
    respuesta = cliente(regional_sureste).patch(
        f"/api/categorias/{categoria.pk}/", {"nombre": "Difusion"}, format="json"
    )
    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_super_admin_si_puede_renombrar(cliente, crear_usuario):
    jefe = crear_usuario("dora_super", Rol.SUPER_ADMIN)
    categoria = Categoria.objects.create(nombre="Comunicación")

    respuesta = cliente(jefe).patch(
        f"/api/categorias/{categoria.pk}/", {"nombre": "Difusión"}, format="json"
    )
    assert respuesta.status_code == 200
    categoria.refresh_from_db()
    assert categoria.nombre == "Difusión"
    assert categoria.nombre_normalizado == "difusion"
