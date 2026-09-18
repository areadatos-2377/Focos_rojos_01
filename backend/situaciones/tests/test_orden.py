"""El orden de importancia es lo mas fragil del sistema.

Estas pruebas deben correr sobre PostgreSQL: lo que se esta verificando es que el
indice unico parcial `uniq_orden_entre_activas_por_entidad` no se viole durante el
reordenamiento. Un `bulk_update` ingenuo fallaria aqui.
"""
import pytest
from django.db.utils import IntegrityError

from situaciones import services
from situaciones.models import Estatus, Situacion


@pytest.mark.django_db
def test_las_situaciones_entran_al_final_del_orden(crear, chiapas, ordenes):
    crear(chiapas, tema="Primera")
    crear(chiapas, tema="Segunda")
    crear(chiapas, tema="Tercera")

    assert ordenes(chiapas) == [("Primera", 1), ("Segunda", 2), ("Tercera", 3)]


@pytest.mark.django_db
def test_el_orden_es_independiente_por_entidad(crear, chiapas, oaxaca, ordenes):
    crear(chiapas, tema="De Chiapas")
    crear(oaxaca, tema="De Oaxaca")

    assert ordenes(chiapas) == [("De Chiapas", 1)]
    assert ordenes(oaxaca) == [("De Oaxaca", 1)]


@pytest.mark.django_db
def test_reordenar_invierte_sin_violar_la_unicidad(crear, chiapas, ordenes):
    """El caso que rompe un bulk_update directo: invertir el orden completo."""
    a = crear(chiapas, tema="Primera")
    b = crear(chiapas, tema="Segunda")
    c = crear(chiapas, tema="Tercera")

    services.reordenar_situaciones(chiapas, [c.pk, b.pk, a.pk])

    assert ordenes(chiapas) == [("Tercera", 1), ("Segunda", 2), ("Primera", 3)]


@pytest.mark.django_db
def test_reordenar_intercambiando_dos_contiguas(crear, chiapas, ordenes):
    """Intercambiar 1 y 2 es el choque mas directo posible contra el indice unico."""
    a = crear(chiapas, tema="Primera")
    b = crear(chiapas, tema="Segunda")

    services.reordenar_situaciones(chiapas, [b.pk, a.pk])

    assert ordenes(chiapas) == [("Segunda", 1), ("Primera", 2)]


@pytest.mark.django_db
def test_reordenar_rechaza_una_lista_incompleta(crear, chiapas, ordenes):
    """Una lista parcial delata una vista desactualizada: aplicarla pisaria a otro usuario."""
    a = crear(chiapas, tema="Primera")
    crear(chiapas, tema="Segunda")

    with pytest.raises(services.OrdenInvalido):
        services.reordenar_situaciones(chiapas, [a.pk])

    assert ordenes(chiapas) == [("Primera", 1), ("Segunda", 2)]


@pytest.mark.django_db
def test_reordenar_rechaza_ids_repetidos(crear, chiapas):
    a = crear(chiapas, tema="Primera")
    b = crear(chiapas, tema="Segunda")

    with pytest.raises(services.OrdenInvalido):
        services.reordenar_situaciones(chiapas, [a.pk, a.pk, b.pk])


@pytest.mark.django_db
def test_reordenar_rechaza_una_situacion_de_otra_entidad(crear, chiapas, oaxaca):
    a = crear(chiapas, tema="De Chiapas")
    ajena = crear(oaxaca, tema="De Oaxaca")

    with pytest.raises(services.OrdenInvalido):
        services.reordenar_situaciones(chiapas, [a.pk, ajena.pk])


@pytest.mark.django_db
def test_cerrar_densifica_el_orden_restante(crear, chiapas, usuario, ordenes):
    crear(chiapas, tema="Primera")
    segunda = crear(chiapas, tema="Segunda")
    crear(chiapas, tema="Tercera")

    services.cerrar_situacion(segunda, usuario=usuario)

    # Sin huecos: la tercera sube al lugar 2.
    assert ordenes(chiapas) == [("Primera", 1), ("Tercera", 2)]

    segunda.refresh_from_db()
    assert segunda.orden is None
    assert segunda.archivada_en is not None
    assert segunda.estatus == Estatus.CERRADA


@pytest.mark.django_db
def test_cerrar_la_primera_recorre_a_todas(crear, chiapas, usuario, ordenes):
    primera = crear(chiapas, tema="Primera")
    crear(chiapas, tema="Segunda")
    crear(chiapas, tema="Tercera")

    services.cerrar_situacion(primera, usuario=usuario)

    assert ordenes(chiapas) == [("Segunda", 1), ("Tercera", 2)]


@pytest.mark.django_db
def test_la_cerrada_sale_de_la_galeria_pero_sigue_consultable(crear, chiapas, usuario):
    situacion = crear(chiapas, tema="Resuelta")
    services.cerrar_situacion(situacion, usuario=usuario)

    assert Situacion.objects.filter(entidad=chiapas).activas().count() == 0
    assert Situacion.objects.filter(entidad=chiapas).archivadas().count() == 1


@pytest.mark.django_db
def test_reabrir_la_coloca_al_final(crear, chiapas, usuario, ordenes):
    primera = crear(chiapas, tema="Primera")
    crear(chiapas, tema="Segunda")

    services.cerrar_situacion(primera, usuario=usuario)
    services.reabrir_situacion(primera, usuario=usuario)

    assert ordenes(chiapas) == [("Segunda", 1), ("Primera", 2)]
    primera.refresh_from_db()
    assert primera.estatus == Estatus.EN_PROCESO
    assert primera.archivada_en is None


@pytest.mark.django_db
def test_cerrar_dos_veces_no_altera_nada(crear, chiapas, usuario, ordenes):
    situacion = crear(chiapas, tema="Primera")
    crear(chiapas, tema="Segunda")

    services.cerrar_situacion(situacion, usuario=usuario)
    services.cerrar_situacion(situacion, usuario=usuario)

    assert ordenes(chiapas) == [("Segunda", 1)]


@pytest.mark.django_db
def test_la_base_impide_dos_activas_con_el_mismo_orden(crear, chiapas):
    """Red de seguridad: aunque alguien escriba `orden` a mano, la base lo bloquea."""
    crear(chiapas, tema="Primera")
    segunda = crear(chiapas, tema="Segunda")

    segunda.orden = 1
    with pytest.raises(IntegrityError):
        segunda.save()


@pytest.mark.django_db
def test_dos_archivadas_pueden_coexistir_sin_orden(crear, chiapas, usuario):
    """El indice es parcial: solo restringe a las activas."""
    a = crear(chiapas, tema="Primera")
    b = crear(chiapas, tema="Segunda")

    services.cerrar_situacion(a, usuario=usuario)
    services.cerrar_situacion(b, usuario=usuario)

    assert Situacion.objects.filter(entidad=chiapas, orden__isnull=True).count() == 2
