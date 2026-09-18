"""Permisos de rol duro (no de alcance por region)."""
from rest_framework.permissions import BasePermission

from core.scoping import es_admin


class EsAdministradorOSuperAdmin(BasePermission):
    message = "Se requiere rol de administrador."

    def has_permission(self, request, view):
        return es_admin(request.user)


class EsSuperAdmin(BasePermission):
    message = "Se requiere rol de super administrador."

    def has_permission(self, request, view):
        from usuarios.models import Rol

        return request.user.is_authenticated and request.user.rol == Rol.SUPER_ADMIN


class SoloLecturaOSuperAdmin(BasePermission):
    """Cualquiera autenticado puede leer y crear; solo super_admin modifica o borra."""

    def has_permission(self, request, view):
        from usuarios.models import Rol

        if not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS", "POST"):
            return True
        return request.user.rol == Rol.SUPER_ADMIN
