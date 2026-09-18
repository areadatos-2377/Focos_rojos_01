"""API de situaciones: alcance por region, galeria, cierre y reordenamiento."""
import pytest

from situaciones import services
from situaciones.models import Situacion


@pytest.mark.django_db
def test_alta_por_api_asigna_el_orden(cliente, usuario, datos_alta):
    respuesta = cliente(usuario).post("/api/situaciones/", datos_alta, format="json")

    assert respuesta.status_code == 201
    assert respuesta.data["orden"] == 1
    assert respuesta.data["entidad_nombre"] == "Chiapas"
    assert respuesta.data["region_nombre"] == "Sureste"


@pytest.mark.django_db
def test_un_regional_no_puede_registrar_en_otra_region(
    cliente, regional_centro, datos_alta
):
    """Chiapas es del Sureste; Beto es del Centro. Debe ser error de validacion."""
    respuesta = cliente(regional_centro).post(
        "/api/situaciones/", datos_alta, format="json"
    )

    assert respuesta.status_code == 400
    assert "entidad" in respuesta.data
    assert Situacion.objects.count() == 0


@pytest.mark.django_db
def test_la_galeria_oculta_las_archivadas(cliente, usuario, crear, chiapas):
    crear(chiapas, tema="Activa")
    cerrada = crear(chiapas, tema="Cerrada")
    services.cerrar_situacion(cerrada, usuario=usuario)

    galeria = cliente(usuario).get("/api/situaciones/?entidad_clave=chiapas")
    assert [s["tema"] for s in galeria.data["results"]] == ["Activa"]

    archivadas = cliente(usuario).get(
        "/api/situaciones/?entidad_clave=chiapas&archivadas=true"
    )
    assert [s["tema"] for s in archivadas.data["results"]] == ["Cerrada"]


@pytest.mark.django_db
def test_un_regional_no_ve_situaciones_de_otra_region(
    cliente, regional_centro, crear, chiapas
):
    crear(chiapas, tema="Secreta del Sureste")

    listado = cliente(regional_centro).get("/api/situaciones/")
    assert listado.data["count"] == 0


@pytest.mark.django_db
def test_una_situacion_ajena_responde_404(cliente, regional_centro, crear, chiapas):
    ajena = crear(chiapas, tema="Secreta del Sureste")

    respuesta = cliente(regional_centro).get(f"/api/situaciones/{ajena.pk}/")
    assert respuesta.status_code == 404


@pytest.mark.django_db
def test_el_administrador_ve_todo(cliente, administrador, crear, chiapas, oaxaca):
    crear(chiapas, tema="De Chiapas")
    crear(oaxaca, tema="De Oaxaca")

    listado = cliente(administrador).get("/api/situaciones/")
    assert listado.data["count"] == 2


@pytest.mark.django_db
def test_no_se_puede_mover_una_situacion_de_entidad(cliente, usuario, crear, chiapas):
    situacion = crear(chiapas)

    respuesta = cliente(usuario).patch(
        f"/api/situaciones/{situacion.pk}/", {"entidad": "oaxaca"}, format="json"
    )
    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_editar_registra_la_bitacora_y_se_puede_consultar(
    cliente, usuario, crear, chiapas
):
    situacion = crear(chiapas, tema="Tema viejo")

    cliente(usuario).patch(
        f"/api/situaciones/{situacion.pk}/", {"tema": "Tema nuevo"}, format="json"
    )

    bitacora = cliente(usuario).get(f"/api/situaciones/{situacion.pk}/bitacora/")
    assert bitacora.status_code == 200
    campos = {m["campo"] for m in bitacora.data}
    assert "tema" in campos

    movimiento = next(m for m in bitacora.data if m["campo"] == "tema")
    assert movimiento["campo_etiqueta"] == "Tema"
    assert movimiento["usuario_nombre"] == "Ana Sureste"


@pytest.mark.django_db
def test_cerrar_por_api_densifica(cliente, usuario, crear, chiapas, ordenes):
    crear(chiapas, tema="Primera")
    segunda = crear(chiapas, tema="Segunda")
    crear(chiapas, tema="Tercera")

    respuesta = cliente(usuario).post(f"/api/situaciones/{segunda.pk}/cerrar/")
    assert respuesta.status_code == 200
    assert respuesta.data["archivada"] is True
    assert ordenes(chiapas) == [("Primera", 1), ("Tercera", 2)]


@pytest.mark.django_db
def test_reordenar_por_api(cliente, usuario, crear, chiapas, ordenes):
    a = crear(chiapas, tema="Primera")
    b = crear(chiapas, tema="Segunda")
    c = crear(chiapas, tema="Tercera")

    respuesta = cliente(usuario).put(
        "/api/entidades/chiapas/orden-situaciones/",
        {"orden": [c.pk, a.pk, b.pk]},
        format="json",
    )

    assert respuesta.status_code == 200
    assert ordenes(chiapas) == [("Tercera", 1), ("Primera", 2), ("Segunda", 3)]


@pytest.mark.django_db
def test_reordenar_con_lista_incompleta_devuelve_409(cliente, usuario, crear, chiapas):
    a = crear(chiapas, tema="Primera")
    crear(chiapas, tema="Segunda")

    respuesta = cliente(usuario).put(
        "/api/entidades/chiapas/orden-situaciones/", {"orden": [a.pk]}, format="json"
    )

    assert respuesta.status_code == 409
    assert "Recarga la vista" in respuesta.data["detalle"]


@pytest.mark.django_db
def test_un_regional_no_puede_reordenar_otra_entidad(
    cliente, regional_centro, crear, chiapas
):
    a = crear(chiapas, tema="Primera")

    respuesta = cliente(regional_centro).put(
        "/api/entidades/chiapas/orden-situaciones/", {"orden": [a.pk]}, format="json"
    )
    assert respuesta.status_code == 404


@pytest.mark.django_db
def test_no_se_puede_borrar_una_situacion(cliente, usuario, crear, chiapas):
    """Las situaciones se cierran, no se borran."""
    situacion = crear(chiapas)

    respuesta = cliente(usuario).delete(f"/api/situaciones/{situacion.pk}/")
    assert respuesta.status_code == 405


@pytest.mark.django_db
def test_sin_autenticar_no_se_ve_nada(cliente):
    assert cliente().get("/api/situaciones/").status_code == 401
