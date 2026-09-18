"""Red de seguridad contra el agujero tipico: agregar un endpoint nuevo meses
despues y olvidar el filtro por region.

Esta prueba recorre TODAS las rutas registradas y exige que cualquier vista cuyo
modelo dependa de Entidad aplique el alcance. No hay que acordarse de nada: si
falta, la suite falla sola.
"""
import pytest
from django.urls import get_resolver

from catalogos.models import Entidad
from core.mixins import AlcanceEntidadMixin

#: Vistas que legitimamente NO filtran por entidad, con el motivo.
#: Agregar algo aqui es una decision consciente, no un descuido.
EXENTAS = {
    "CategoriaViewSet": "El catalogo de categorias es global y compartido.",
    "RegionViewSet": "Filtra por region directamente, no por entidad.",
    "UsuarioViewSet": "Gestion de cuentas; su permiso es de rol, no de alcance.",
}


def _vistas_registradas():
    """Todas las clases de vista alcanzables desde el urlconf raiz."""
    vistas = {}
    for patron in get_resolver().url_patterns:
        _recolectar(patron, vistas)
    return vistas


def _recolectar(patron, vistas):
    if hasattr(patron, "url_patterns"):
        for hijo in patron.url_patterns:
            _recolectar(hijo, vistas)
        return
    callback = getattr(patron, "callback", None)
    clase = getattr(callback, "cls", None) or getattr(callback, "view_class", None)
    if clase is not None:
        vistas[clase.__name__] = clase


def _depende_de_entidad(modelo) -> bool:
    """El modelo es Entidad o tiene un camino de FKs hacia ella."""
    if modelo is Entidad:
        return True
    return any(
        campo.is_relation and campo.related_model is Entidad
        for campo in modelo._meta.get_fields()
    )


@pytest.mark.parametrize("nombre,clase", sorted(_vistas_registradas().items()))
def test_las_vistas_ligadas_a_entidad_aplican_el_alcance(nombre, clase):
    queryset = getattr(clase, "queryset", None)
    if queryset is None:
        pytest.skip(f"{nombre} no declara queryset.")

    if not _depende_de_entidad(queryset.model):
        pytest.skip(f"{nombre} no depende de Entidad.")

    if nombre in EXENTAS:
        pytest.skip(f"{nombre} exenta: {EXENTAS[nombre]}")

    assert issubclass(clase, AlcanceEntidadMixin), (
        f"{nombre} expone {queryset.model.__name__}, que depende de Entidad, pero no "
        f"hereda AlcanceEntidadMixin: cualquier usuario veria datos de otras regiones. "
        f"Hereda el mixin, o agrega {nombre} a EXENTAS con el motivo."
    )


def test_el_recolector_encuentra_vistas():
    """Si el recolector dejara de encontrar vistas, la prueba de arriba pasaria en
    vacio y el agujero quedaria abierto sin que nadie se entere."""
    vistas = _vistas_registradas()
    assert "SituacionViewSet" in vistas
    assert "EntidadViewSet" in vistas
