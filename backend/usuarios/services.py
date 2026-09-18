"""Registro de accesos. Es la unica pieza que escribe `ultimo_acceso`."""
from django.db import transaction
from django.utils import timezone

from .models import RegistroAcceso


def ip_del_request(request) -> str | None:
    """Detras del proxy de Railway la IP real viene en X-Forwarded-For."""
    reenviada = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if reenviada:
        return reenviada.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


@transaction.atomic
def registrar_acceso(usuario, request) -> RegistroAcceso:
    ahora = timezone.now()
    acceso = RegistroAcceso.objects.create(
        usuario=usuario,
        ip=ip_del_request(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:300],
    )
    usuario.ultimo_acceso = ahora
    usuario.save(update_fields=["ultimo_acceso"])
    return acceso
