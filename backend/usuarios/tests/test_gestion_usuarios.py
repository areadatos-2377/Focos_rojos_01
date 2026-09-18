"""Solo el super administrador crea cuentas; los administradores solo consultan."""
import pytest

from usuarios.models import Rol, Usuario


@pytest.fixture
def super_admin(crear_usuario):
    return crear_usuario("dora_super", Rol.SUPER_ADMIN)


@pytest.mark.django_db
def test_super_admin_crea_una_cuenta_regional(cliente, super_admin, catalogo):
    respuesta = cliente(super_admin).post(
        "/api/usuarios/",
        {
            "username": "nuevo_regional",
            "nombre_completo": "Nuevo Regional",
            "rol": Rol.REGIONAL,
            "region": catalogo["noroeste"].pk,
            "password": "clave-inicial-2026",
        },
        format="json",
    )
    assert respuesta.status_code == 201
    creado = Usuario.objects.get(username="nuevo_regional")
    assert creado.region.clave == "noroeste"
    assert creado.check_password("clave-inicial-2026")


@pytest.mark.django_db
def test_no_se_puede_crear_un_regional_sin_region(cliente, super_admin):
    respuesta = cliente(super_admin).post(
        "/api/usuarios/",
        {"username": "huerfano", "rol": Rol.REGIONAL, "password": "clave-inicial-2026"},
        format="json",
    )
    assert respuesta.status_code == 400
    assert "region" in respuesta.data


@pytest.mark.django_db
def test_administrador_puede_listar_pero_no_crear(cliente, administrador, catalogo):
    assert cliente(administrador).get("/api/usuarios/").status_code == 200

    respuesta = cliente(administrador).post(
        "/api/usuarios/",
        {"username": "intruso", "rol": Rol.ADMINISTRADOR, "password": "clave-inicial-2026"},
        format="json",
    )
    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_regional_no_puede_ver_el_listado_de_usuarios(cliente, regional_sureste):
    assert cliente(regional_sureste).get("/api/usuarios/").status_code == 403


@pytest.mark.django_db
def test_solo_los_admin_ven_el_historial_de_accesos(cliente, regional_sureste, administrador):
    assert cliente(regional_sureste).get("/api/auditoria/accesos/").status_code == 403
    assert cliente(administrador).get("/api/auditoria/accesos/").status_code == 200


@pytest.mark.django_db
def test_rol_no_regional_no_conserva_region(cliente, super_admin, catalogo):
    """Un usuario que deja de ser regional no debe arrastrar su region anterior."""
    usuario = Usuario.objects.create_user(
        username="cambia_rol", password="clave-inicial-2026",
        rol=Rol.REGIONAL, region=catalogo["centro"],
    )
    respuesta = cliente(super_admin).patch(
        f"/api/usuarios/{usuario.pk}/", {"rol": Rol.ADMINISTRADOR}, format="json"
    )
    assert respuesta.status_code == 200
    usuario.refresh_from_db()
    assert usuario.region is None
