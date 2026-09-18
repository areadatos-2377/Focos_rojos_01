"""Endpoint de vista previa: valida la seleccion, respeta el alcance por region y
devuelve el documento sin guardar nada."""
import datetime as dt

import pytest

from catalogos.models import Categoria, Entidad, Region
from situaciones import services as servicios_situacion
from usuarios.models import Rol, Usuario

URL = "/api/reportes/vista-previa/"


@pytest.fixture
def entorno(db):
    from django.core.management import call_command

    call_command("seed_catalogos")
    sureste = Region.objects.get(clave="sureste")
    chiapas = Entidad.objects.get(clave="chiapas")
    categoria = Categoria.objects.create(nombre="Infraestructura")
    usuario = Usuario.objects.create_user(
        username="ana", password="prueba-segura-123", nombre_completo="Ana Lopez",
        rol=Rol.REGIONAL, region=sureste,
    )

    situaciones = [
        servicios_situacion.crear_situacion(
            usuario=usuario,
            entidad=chiapas,
            categoria=categoria,
            tema=f"Situacion {i}",
            fecha_inicio=dt.date(2026, 5, 2),
            estatus_detalle="Pendiente.",
            acciones="En gestion.",
            responsable="Ing. Perez",
            fecha_estimada_solucion=dt.date(2026, 10, 15),
        )
        for i in range(1, 7)
    ]
    return {
        "usuario": usuario, "chiapas": chiapas,
        "categoria": categoria, "situaciones": situaciones,
    }


@pytest.fixture
def cliente():
    from rest_framework.test import APIClient

    def _cliente(usuario=None):
        c = APIClient()
        if usuario is not None:
            c.force_authenticate(user=usuario)
        return c

    return _cliente


def cuerpo(entorno, **extra):
    datos = {
        "entidad": "chiapas",
        "fecha_entrega": "2026-08-16",
        "responsable_reporte": "Dr. Juan Ramirez",
        "fecha_corte": "2026-08-14",
        "situaciones": [s.pk for s in entorno["situaciones"][:3]],
    }
    datos.update(extra)
    return datos


@pytest.mark.django_db
def test_devuelve_un_pdf(cliente, entorno):
    respuesta = cliente(entorno["usuario"]).post(URL, cuerpo(entorno), format="json")

    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == "application/pdf"
    assert respuesta.content[:5] == b"%PDF-"
    assert "inline" in respuesta["Content-Disposition"]
    assert "focos-rojos_chiapas_2026-08-14.pdf" in respuesta["Content-Disposition"]


@pytest.mark.django_db
def test_devuelve_docx_si_se_pide(cliente, entorno):
    respuesta = cliente(entorno["usuario"]).post(
        URL, cuerpo(entorno, formato="docx"), format="json"
    )

    assert respuesta.status_code == 200
    assert respuesta.content[:2] == b"PK"  # un .docx es un zip


@pytest.mark.django_db
def test_no_guarda_nada(cliente, entorno):
    """La vista previa no debe dejar rastro: para eso esta el guardado explicito."""
    from situaciones.models import Situacion

    antes = Situacion.objects.count()
    cliente(entorno["usuario"]).post(URL, cuerpo(entorno), format="json")
    assert Situacion.objects.count() == antes


@pytest.mark.django_db
def test_rechaza_mas_de_cinco_situaciones(cliente, entorno):
    respuesta = cliente(entorno["usuario"]).post(
        URL, cuerpo(entorno, situaciones=[s.pk for s in entorno["situaciones"]]),
        format="json",
    )
    assert respuesta.status_code == 400
    assert "situaciones" in respuesta.data


@pytest.mark.django_db
def test_rechaza_una_seleccion_vacia(cliente, entorno):
    respuesta = cliente(entorno["usuario"]).post(
        URL, cuerpo(entorno, situaciones=[]), format="json"
    )
    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_rechaza_situaciones_de_otra_entidad(cliente, entorno):
    """Una situacion de Oaxaca no puede colarse en el reporte de Chiapas."""
    oaxaca = Entidad.objects.get(clave="oaxaca")
    ajena = servicios_situacion.crear_situacion(
        usuario=entorno["usuario"], entidad=oaxaca, categoria=entorno["categoria"],
        tema="De Oaxaca", fecha_inicio=dt.date(2026, 5, 2),
        estatus_detalle="x", acciones="y", responsable="z",
    )

    respuesta = cliente(entorno["usuario"]).post(
        URL, cuerpo(entorno, situaciones=[ajena.pk]), format="json"
    )
    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_rechaza_situaciones_archivadas(cliente, entorno):
    cerrada = entorno["situaciones"][0]
    servicios_situacion.cerrar_situacion(cerrada, usuario=entorno["usuario"])

    respuesta = cliente(entorno["usuario"]).post(
        URL, cuerpo(entorno, situaciones=[cerrada.pk]), format="json"
    )
    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_un_regional_no_puede_generar_de_otra_region(cliente, entorno, db):
    centro = Region.objects.get(clave="centro")
    forastero = Usuario.objects.create_user(
        username="beto", password="prueba-segura-123", rol=Rol.REGIONAL, region=centro,
    )

    respuesta = cliente(forastero).post(URL, cuerpo(entorno), format="json")
    assert respuesta.status_code == 400
    assert "entidad" in respuesta.data


@pytest.mark.django_db
def test_la_entrega_no_puede_ser_antes_del_corte(cliente, entorno):
    respuesta = cliente(entorno["usuario"]).post(
        URL, cuerpo(entorno, fecha_entrega="2026-08-01", fecha_corte="2026-08-14"),
        format="json",
    )
    assert respuesta.status_code == 400
    assert "fecha_entrega" in respuesta.data


@pytest.mark.django_db
def test_requiere_autenticacion(cliente, entorno):
    assert cliente().post(URL, cuerpo(entorno), format="json").status_code == 401


@pytest.mark.django_db
def test_el_orden_de_la_seleccion_manda(cliente, entorno):
    """El orden de la lista define cual sale como SITUACION 1, no el orden guardado."""
    from docx import Document
    import io

    tercera, primera = entorno["situaciones"][2], entorno["situaciones"][0]
    respuesta = cliente(entorno["usuario"]).post(
        URL, cuerpo(entorno, situaciones=[tercera.pk, primera.pk], formato="docx"),
        format="json",
    )

    documento = Document(io.BytesIO(respuesta.content))
    assert documento.tables[1].rows[1].cells[1].text == tercera.tema
    assert documento.tables[2].rows[1].cells[1].text == primera.tema
