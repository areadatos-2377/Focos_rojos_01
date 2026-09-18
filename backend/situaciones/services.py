"""Toda la logica de orden de importancia y de bitacora.

Ni las vistas ni `Model.save()` deben tocar `orden`: hacerlo desde dos lugares es
como se rompe la numeracion. Entra siempre por aqui.
"""
from django.db import transaction
from django.db.models import F, Max
from django.utils import timezone

from .models import AccionBitacora, BitacoraSituacion, Estatus, Situacion

#: Desplazamiento temporal para reordenar sin violar el indice unico parcial.
#: PostgreSQL no admite DEFERRABLE en un indice unico parcial, asi que no se puede
#: reasignar 1..N de golpe: primero se mueve todo fuera del rango en uso.
DESPLAZAMIENTO = 10_000

#: Campos cuyo cambio se registra en la bitacora, con su etiqueta legible.
CAMPOS_AUDITADOS = {
    "categoria": "Categoria",
    "tema": "Tema",
    "fecha_inicio": "Fecha de inicio",
    "estatus": "Estatus",
    "estatus_detalle": "Estatus actual",
    "acciones": "Acciones que se estan realizando",
    "responsable": "Responsable",
    "fecha_estimada_solucion": "Fecha estimada de solucion",
}


def _a_texto(situacion: Situacion, campo: str) -> str | None:
    """Valor de un campo como texto legible y estable en el tiempo.

    La categoria se guarda por su nombre (no su id) para que la bitacora siga
    teniendo sentido si mas tarde se renombra o se fusiona.
    """
    valor = getattr(situacion, campo)
    if valor is None or valor == "":
        return None
    if campo == "categoria":
        return valor.nombre
    if campo == "estatus":
        return Estatus(valor).label
    if campo in ("fecha_inicio", "fecha_estimada_solucion"):
        return valor.isoformat()
    return str(valor)


def _siguiente_orden(entidad_id: int) -> int:
    maximo = (
        Situacion.objects.filter(entidad_id=entidad_id)
        .activas()
        .aggregate(maximo=Max("orden"))["maximo"]
    )
    return (maximo or 0) + 1


def _bloquear_activas(entidad_id: int):
    """Bloquea las filas activas de la entidad para evitar carreras entre usuarios."""
    return (
        Situacion.objects.select_for_update()
        .filter(entidad_id=entidad_id)
        .activas()
        .order_by("orden")
    )


def _reasignar(situaciones, orden_deseado: list[int]) -> None:
    """Reescribe el orden en dos fases para no chocar con el indice unico parcial.

    Fase 1: desplazar todo +DESPLAZAMIENTO (siguen siendo unicos entre si).
    Fase 2: asignar 1..N segun `orden_deseado`.
    """
    por_id = {s.pk: s for s in situaciones}

    Situacion.objects.filter(pk__in=por_id).update(orden=F("orden") + DESPLAZAMIENTO)

    for posicion, pk in enumerate(orden_deseado, start=1):
        por_id[pk].orden = posicion
    Situacion.objects.bulk_update(por_id.values(), ["orden"])


def _densificar(entidad_id: int) -> None:
    """Deja el orden de las activas en 1..N sin huecos, respetando el orden actual."""
    activas = list(_bloquear_activas(entidad_id))
    if not activas:
        return
    _reasignar(activas, [s.pk for s in activas])


@transaction.atomic
def crear_situacion(*, usuario, **datos) -> Situacion:
    """Alta. La situacion entra al final del orden; el usuario la reacomoda arrastrando."""
    entidad = datos["entidad"]
    # Bloquea para que dos altas simultaneas no reclamen el mismo numero de orden.
    list(_bloquear_activas(entidad.pk))

    situacion = Situacion.objects.create(
        creada_por=usuario,
        actualizada_por=usuario,
        orden=_siguiente_orden(entidad.pk),
        **datos,
    )
    BitacoraSituacion.objects.create(
        situacion=situacion, usuario=usuario, accion=AccionBitacora.CREACION
    )
    return situacion


@transaction.atomic
def actualizar_situacion(situacion: Situacion, *, usuario, **datos) -> Situacion:
    """Edicion con bitacora campo a campo.

    El cambio de estatus a CERRADA (o desde ella) NO se maneja aqui: para eso estan
    `cerrar_situacion` y `reabrir_situacion`, que ademas ajustan el orden.
    """
    anterior = Situacion.objects.select_related("categoria").get(pk=situacion.pk)

    movimientos = []
    for campo in CAMPOS_AUDITADOS:
        if campo not in datos:
            continue
        setattr(situacion, campo, datos[campo])
        valor_antes = _a_texto(anterior, campo)
        valor_despues = _a_texto(situacion, campo)
        if valor_antes != valor_despues:
            movimientos.append(
                BitacoraSituacion(
                    situacion=situacion,
                    usuario=usuario,
                    accion=(
                        AccionBitacora.CAMBIO_ESTATUS
                        if campo == "estatus"
                        else AccionBitacora.EDICION
                    ),
                    campo=campo,
                    valor_anterior=valor_antes,
                    valor_nuevo=valor_despues,
                )
            )

    if not movimientos:
        return situacion

    situacion.actualizada_por = usuario
    situacion.save()
    BitacoraSituacion.objects.bulk_create(movimientos)
    return situacion


@transaction.atomic
def cerrar_situacion(situacion: Situacion, *, usuario) -> Situacion:
    """Archiva la situacion: sale de la galeria y suelta su lugar en el orden."""
    if situacion.esta_archivada:
        return situacion

    entidad_id = situacion.entidad_id
    orden_previo = situacion.orden

    situacion.estatus = Estatus.CERRADA
    situacion.archivada_en = timezone.now()
    situacion.orden = None
    situacion.actualizada_por = usuario
    situacion.save()

    _densificar(entidad_id)

    BitacoraSituacion.objects.create(
        situacion=situacion,
        usuario=usuario,
        accion=AccionBitacora.CIERRE,
        campo="estatus",
        valor_anterior=f"Activa (orden {orden_previo})",
        valor_nuevo=Estatus.CERRADA.label,
    )
    return situacion


@transaction.atomic
def reabrir_situacion(
    situacion: Situacion, *, usuario, estatus: str = Estatus.EN_PROCESO
) -> Situacion:
    """Vuelve a poner la situacion en la galeria, al final del orden."""
    if not situacion.esta_archivada:
        return situacion

    entidad_id = situacion.entidad_id
    list(_bloquear_activas(entidad_id))

    situacion.estatus = estatus
    situacion.archivada_en = None
    situacion.orden = _siguiente_orden(entidad_id)
    situacion.actualizada_por = usuario
    situacion.save()

    BitacoraSituacion.objects.create(
        situacion=situacion,
        usuario=usuario,
        accion=AccionBitacora.REAPERTURA,
        campo="estatus",
        valor_anterior=Estatus.CERRADA.label,
        valor_nuevo=Estatus(estatus).label,
    )
    return situacion


class OrdenInvalido(ValueError):
    """La lista recibida no coincide con las situaciones activas de la entidad."""


@transaction.atomic
def reordenar_situaciones(entidad, ids_en_orden: list[int]) -> list[Situacion]:
    """Reordena TODAS las activas de la entidad.

    Se exige la lista completa a proposito: si llega parcial, quien la envio estaba
    viendo una version desactualizada y aplicarla pisaria el trabajo de otro usuario.
    El reordenamiento no genera bitacora (es ajuste de prioridad, no un cambio de datos).
    """
    activas = list(_bloquear_activas(entidad.pk))
    ids_actuales = {s.pk for s in activas}
    ids_recibidos = list(dict.fromkeys(ids_en_orden))

    if len(ids_recibidos) != len(ids_en_orden):
        raise OrdenInvalido("La lista de orden tiene identificadores repetidos.")
    if set(ids_recibidos) != ids_actuales:
        faltan = len(ids_actuales - set(ids_recibidos))
        sobran = len(set(ids_recibidos) - ids_actuales)
        raise OrdenInvalido(
            "La lista debe incluir exactamente las situaciones activas de la entidad "
            f"(faltan {faltan}, sobran {sobran}). Recarga la vista e intenta de nuevo."
        )

    _reasignar(activas, ids_recibidos)
    return list(Situacion.objects.filter(pk__in=ids_actuales).order_by("orden"))
