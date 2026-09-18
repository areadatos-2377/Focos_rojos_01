import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from catalogos.models import Region
from usuarios.models import Rol, Usuario


@pytest.fixture
def catalogo(db):
    call_command("seed_catalogos")
    return {r.clave: r for r in Region.objects.all()}


@pytest.fixture
def crear_usuario(db, catalogo):
    def _crear(username, rol, region_clave=None):
        return Usuario.objects.create_user(
            username=username,
            password="prueba-segura-123",
            nombre_completo=username.title(),
            rol=rol,
            region=catalogo[region_clave] if region_clave else None,
        )

    return _crear


@pytest.fixture
def regional_sureste(crear_usuario):
    return crear_usuario("ana_sureste", Rol.REGIONAL, "sureste")


@pytest.fixture
def regional_centro(crear_usuario):
    return crear_usuario("beto_centro", Rol.REGIONAL, "centro")


@pytest.fixture
def administrador(crear_usuario):
    return crear_usuario("carla_admin", Rol.ADMINISTRADOR)


@pytest.fixture
def cliente():
    def _cliente(usuario=None):
        c = APIClient()
        if usuario is not None:
            c.force_authenticate(user=usuario)
        return c

    return _cliente
