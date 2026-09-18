"""Punto unico del filtro RBAC por region.

Ninguna vista debe reimplementar esta regla. Si necesitas limitar un queryset por
la region del usuario, usa `entidades_visibles` o el mixin de `core.mixins`.
"""
from django.db.models import QuerySet


def entidades_visibles(usuario) -> QuerySet:
    """Entidades que el usuario tiene derecho a ver.

    - REGIONAL: solo las de su region.
    - ADMINISTRADOR y SUPER_ADMIN: todas las activas.
    """
    from catalogos.models import Entidad
    from usuarios.models import Rol

    qs = Entidad.objects.filter(activa=True)
    if not usuario.is_authenticated:
        return qs.none()
    if usuario.rol == Rol.REGIONAL:
        return qs.filter(region_id=usuario.region_id)
    return qs


def es_admin(usuario) -> bool:
    from usuarios.models import Rol

    return usuario.is_authenticated and usuario.rol in (Rol.ADMINISTRADOR, Rol.SUPER_ADMIN)
