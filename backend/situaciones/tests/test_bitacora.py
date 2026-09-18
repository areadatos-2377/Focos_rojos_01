"""La bitacora es campo a campo: quien, cuando, que campo, valor anterior y nuevo."""
import datetime as dt

import pytest

from situaciones import services
from situaciones.models import AccionBitacora, Estatus


@pytest.mark.django_db
def test_el_alta_deja_un_solo_movimiento(crear, chiapas, usuario):
    situacion = crear(chiapas)

    movimientos = list(situacion.bitacora.all())
    assert len(movimientos) == 1
    assert movimientos[0].accion == AccionBitacora.CREACION
    assert movimientos[0].usuario == usuario
    assert movimientos[0].campo == ""


@pytest.mark.django_db
def test_se_registra_una_linea_por_campo_modificado(crear, chiapas, usuario):
    situacion = crear(chiapas, tema="Tema viejo")

    services.actualizar_situacion(
        situacion,
        usuario=usuario,
        tema="Tema nuevo",
        responsable="Lic. Ramirez",
    )

    ediciones = situacion.bitacora.filter(accion=AccionBitacora.EDICION)
    assert {m.campo for m in ediciones} == {"tema", "responsable"}

    cambio_tema = ediciones.get(campo="tema")
    assert cambio_tema.valor_anterior == "Tema viejo"
    assert cambio_tema.valor_nuevo == "Tema nuevo"


@pytest.mark.django_db
def test_guardar_sin_cambios_no_ensucia_la_bitacora(crear, chiapas, usuario):
    situacion = crear(chiapas, tema="Igual")

    services.actualizar_situacion(situacion, usuario=usuario, tema="Igual")

    assert situacion.bitacora.count() == 1  # solo la creacion


@pytest.mark.django_db
def test_el_cambio_de_estatus_se_marca_aparte(crear, chiapas, usuario):
    situacion = crear(chiapas)

    services.actualizar_situacion(
        situacion, usuario=usuario, estatus=Estatus.EN_PROCESO
    )

    movimiento = situacion.bitacora.get(accion=AccionBitacora.CAMBIO_ESTATUS)
    assert movimiento.valor_anterior == "Abierta"
    assert movimiento.valor_nuevo == "En proceso"


@pytest.mark.django_db
def test_la_categoria_se_guarda_por_nombre_no_por_id(
    crear, chiapas, usuario, otra_categoria
):
    """Asi el historial sigue siendo legible si luego se renombra o fusiona la categoria."""
    situacion = crear(chiapas)

    services.actualizar_situacion(situacion, usuario=usuario, categoria=otra_categoria)

    movimiento = situacion.bitacora.get(campo="categoria")
    assert movimiento.valor_anterior == "Infraestructura"
    assert movimiento.valor_nuevo == "Logística"

    # Se renombra la categoria: el historial no se altera.
    otra_categoria.nombre = "Logística y transporte"
    otra_categoria.save()
    movimiento.refresh_from_db()
    assert movimiento.valor_nuevo == "Logística"


@pytest.mark.django_db
def test_las_fechas_se_guardan_en_formato_estable(crear, chiapas, usuario):
    situacion = crear(chiapas)

    services.actualizar_situacion(
        situacion, usuario=usuario, fecha_estimada_solucion=dt.date(2026, 12, 1)
    )

    movimiento = situacion.bitacora.get(campo="fecha_estimada_solucion")
    assert movimiento.valor_anterior == "2026-09-30"
    assert movimiento.valor_nuevo == "2026-12-01"


@pytest.mark.django_db
def test_el_cierre_y_la_reapertura_quedan_registrados(crear, chiapas, usuario):
    situacion = crear(chiapas)

    services.cerrar_situacion(situacion, usuario=usuario)
    assert situacion.bitacora.filter(accion=AccionBitacora.CIERRE).exists()

    services.reabrir_situacion(situacion, usuario=usuario)
    assert situacion.bitacora.filter(accion=AccionBitacora.REAPERTURA).exists()


@pytest.mark.django_db
def test_el_reordenamiento_no_genera_bitacora(crear, chiapas):
    a = crear(chiapas, tema="Primera")
    b = crear(chiapas, tema="Segunda")
    movimientos_antes = a.bitacora.count() + b.bitacora.count()

    services.reordenar_situaciones(chiapas, [b.pk, a.pk])

    assert a.bitacora.count() + b.bitacora.count() == movimientos_antes


@pytest.mark.django_db
def test_se_conserva_quien_edito_por_ultima_vez(crear, chiapas, usuario, catalogo):
    from usuarios.models import Rol, Usuario

    otro = Usuario.objects.create_user(
        username="beto", password="prueba-segura-123",
        rol=Rol.REGIONAL, region=catalogo["sureste"],
    )
    situacion = crear(chiapas)
    assert situacion.creada_por == usuario

    services.actualizar_situacion(situacion, usuario=otro, tema="Editado por Beto")

    situacion.refresh_from_db()
    assert situacion.creada_por == usuario
    assert situacion.actualizada_por == otro
