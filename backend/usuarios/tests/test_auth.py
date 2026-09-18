"""Login, perfil y registro de accesos."""
import pytest

from usuarios.models import RegistroAcceso, Rol


@pytest.mark.django_db
def test_login_devuelve_tokens_y_perfil(cliente, regional_sureste):
    respuesta = cliente().post(
        "/api/auth/login/",
        {"username": "ana_sureste", "password": "prueba-segura-123"},
        format="json",
    )
    assert respuesta.status_code == 200
    assert "access" in respuesta.data and "refresh" in respuesta.data

    perfil = respuesta.data["usuario"]
    assert perfil["rol"] == Rol.REGIONAL
    assert perfil["region"]["clave"] == "sureste"
    # El perfil ya trae las entidades que puede tocar: el frontend no tiene que preguntarlo aparte.
    assert len(perfil["entidades"]) == 6


@pytest.mark.django_db
def test_login_exitoso_deja_constancia_del_acceso(cliente, regional_sureste):
    assert regional_sureste.ultimo_acceso is None

    cliente().post(
        "/api/auth/login/",
        {"username": "ana_sureste", "password": "prueba-segura-123"},
        format="json",
    )

    regional_sureste.refresh_from_db()
    assert regional_sureste.ultimo_acceso is not None
    assert RegistroAcceso.objects.filter(usuario=regional_sureste).count() == 1


@pytest.mark.django_db
def test_login_fallido_no_deja_constancia(cliente, regional_sureste):
    respuesta = cliente().post(
        "/api/auth/login/",
        {"username": "ana_sureste", "password": "equivocada"},
        format="json",
    )
    assert respuesta.status_code == 401
    assert RegistroAcceso.objects.count() == 0

    regional_sureste.refresh_from_db()
    assert regional_sureste.ultimo_acceso is None


@pytest.mark.django_db
def test_yo_devuelve_el_alcance_del_usuario(cliente, administrador):
    respuesta = cliente(administrador).get("/api/auth/yo/")
    assert respuesta.status_code == 200
    assert respuesta.data["rol"] == Rol.ADMINISTRADOR
    assert respuesta.data["region"] is None
    assert len(respuesta.data["entidades"]) == 24


@pytest.mark.django_db
def test_yo_requiere_autenticacion(cliente):
    assert cliente().get("/api/auth/yo/").status_code == 401


@pytest.mark.django_db
def test_cambiar_password(cliente, regional_sureste):
    respuesta = cliente(regional_sureste).post(
        "/api/auth/cambiar-password/",
        {"password_actual": "prueba-segura-123", "password_nueva": "otra-clave-mejor-99"},
        format="json",
    )
    assert respuesta.status_code == 200

    regional_sureste.refresh_from_db()
    assert regional_sureste.check_password("otra-clave-mejor-99")


@pytest.mark.django_db
def test_cambiar_password_con_actual_incorrecta_falla(cliente, regional_sureste):
    respuesta = cliente(regional_sureste).post(
        "/api/auth/cambiar-password/",
        {"password_actual": "no-es-esta", "password_nueva": "otra-clave-mejor-99"},
        format="json",
    )
    assert respuesta.status_code == 400
