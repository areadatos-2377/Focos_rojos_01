import datetime as dt

import pytest
from django.core.management import call_command

from catalogos.models import Categoria, Entidad, Region
from situaciones import services
from usuarios.models import Rol, Usuario


@pytest.fixture
def catalogo(db):
    call_command("seed_catalogos")
    return {r.clave: r for r in Region.objects.all()}


@pytest.fixture
def chiapas(catalogo):
    return Entidad.objects.get(clave="chiapas")


@pytest.fixture
def oaxaca(catalogo):
    return Entidad.objects.get(clave="oaxaca")


@pytest.fixture
def categoria(db):
    return Categoria.objects.create(nombre="Infraestructura")


@pytest.fixture
def otra_categoria(db):
    return Categoria.objects.create(nombre="Logística")


@pytest.fixture
def usuario(catalogo):
    return Usuario.objects.create_user(
        username="ana_sureste",
        password="prueba-segura-123",
        nombre_completo="Ana Sureste",
        rol=Rol.REGIONAL,
        region=catalogo["sureste"],
    )


@pytest.fixture
def crear(usuario, categoria):
    """Crea una situacion con valores razonables; solo se pasa lo que importa al test."""

    def _crear(entidad, tema="Desabasto de insumos", **extra):
        datos = {
            "entidad": entidad,
            "categoria": categoria,
            "tema": tema,
            "fecha_inicio": dt.date(2026, 5, 2),
            "estatus_detalle": "Sin avance desde la semana pasada.",
            "acciones": "Se solicito apoyo a la coordinacion estatal.",
            "responsable": "Ing. Perez",
            "fecha_estimada_solucion": dt.date(2026, 9, 30),
        }
        datos.update(extra)
        return services.crear_situacion(usuario=usuario, **datos)

    return _crear


@pytest.fixture
def ordenes():
    """Devuelve (tema, orden) de las activas de una entidad, ya ordenadas."""

    def _ordenes(entidad):
        from situaciones.models import Situacion

        return list(
            Situacion.objects.filter(entidad=entidad)
            .activas()
            .order_by("orden")
            .values_list("tema", "orden")
        )

    return _ordenes


@pytest.fixture
def cliente():
    from rest_framework.test import APIClient

    def _cliente(usuario=None):
        c = APIClient()
        if usuario is not None:
            c.force_authenticate(user=usuario)
        return c

    return _cliente


@pytest.fixture
def regional_centro(catalogo):
    return Usuario.objects.create_user(
        username="beto_centro", password="prueba-segura-123",
        nombre_completo="Beto Centro", rol=Rol.REGIONAL, region=catalogo["centro"],
    )


@pytest.fixture
def administrador(catalogo):
    return Usuario.objects.create_user(
        username="carla_admin", password="prueba-segura-123",
        nombre_completo="Carla Admin", rol=Rol.ADMINISTRADOR,
    )


@pytest.fixture
def datos_alta(categoria):
    """Cuerpo valido para POST /api/situaciones/."""
    return {
        "entidad": "chiapas",
        "categoria": categoria.pk,
        "tema": "Falta de personal de enfermeria",
        "fecha_inicio": "2026-05-02",
        "estatus": "ABIERTA",
        "estatus_detalle": "Tres plazas vacantes desde marzo.",
        "acciones": "Se publico la convocatoria estatal.",
        "responsable": "Lic. Gomez",
        "fecha_estimada_solucion": "2026-10-15",
    }
