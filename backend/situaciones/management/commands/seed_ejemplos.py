"""Situaciones de ejemplo para poder mostrar la aplicacion con contenido realista.

El estilo y las categorias estan tomados de `legacy/Formato_Focos_Rojos_Gira_ejemplo.docx`:
el "tema" enumera varios puntos con cifras, la fecha de inicio suele venir vacia y el
responsable es un area, no una persona.

DATOS FICTICIOS. No usar en produccion: `--limpiar` borra todas las situaciones.
"""
import datetime as dt

from django.core.management.base import BaseCommand
from django.db import transaction

from catalogos.models import Categoria, Entidad
from situaciones.models import BitacoraSituacion, Estatus, Situacion
from usuarios.models import Usuario

CATEGORIAS = [
    "Recursos Humanos",
    "Abasto",
    "Servicios Generales",
    "Pasivos",
    "Infraestructura",
    "Logística",
    "Seguridad",
]

# (entidad, categoria, tema, estatus, detalle, acciones, responsable, fecha_inicio)
EJEMPLOS = [
    # ---------------- Noroeste ----------------
    (
        "sinaloa", "Recursos Humanos",
        "Liberación de 488 plazas por jubilaciones, fallecimientos y renuncias.\n"
        "9 trabajadores pendientes de reincorporación a su plaza de base (por ocupar "
        "puestos de confianza, residencias y motivos personales).\n"
        "Pendientes de bajas ante el ISSSTE.\n"
        "8 jefaturas de oficina de la Estructura Estatal pendientes por contratar.",
        Estatus.ABIERTA, "En espera.",
        "Gestiones ante la Coordinación de RH.",
        "Coordinación de Recursos Humanos.", None,
    ),
    (
        "sinaloa", "Abasto",
        "Claves totales 1503, de las cuales 724 se encuentran en 0.\n"
        "328 claves prioritarias que no tenemos en unidades de salud.\n"
        "Desabasto de 15 claves oncológicas en HGC, HPS e ISCAN.\n"
        "Material de curación fuera de cuadro básico.",
        Estatus.EN_PROCESO, "En espera de surtimiento.",
        "Seguimiento a oficios de solicitud de surtimiento.",
        "Coordinación de Recursos Materiales.", None,
    ),
    (
        "sinaloa", "Servicios Generales",
        "Servicio de Gas LP suspendido por falta de pago de los meses de diciembre de "
        "2025, marzo, abril, mayo, junio y julio de 2026.\n"
        "Diésel para plantas de emergencia: peligra la continuidad de los servicios "
        "por falta de pago de marzo a julio de 2026.\n"
        "Suficiencias presupuestarias NO autorizadas.",
        Estatus.ABIERTA, "En espera.",
        "Seguimiento a oficios de solicitudes de pago a la Coordinación de Finanzas.",
        "Coordinación de Finanzas.", dt.date(2025, 12, 1),
    ),
    (
        "sinaloa", "Pasivos",
        "Pagos pendientes 2025 a 2 proveedores por $759,777.55:\n"
        "Servicios Generales $398,230.36 y Servicios Médicos Integrales $361,547.19.\n"
        "Pagos pendientes 2026 a 13 proveedores por $125.5 mdp:\n"
        "Servicios Generales $5.5 mdp y Servicios Médicos Integrales $120 mdp.",
        Estatus.ABIERTA, "En espera.",
        "Seguimiento a oficios de solicitudes de pago ante la Coordinación de Finanzas.",
        "Coordinación de Finanzas.", None,
    ),
    (
        "sinaloa", "Infraestructura",
        "La sustitución del Hospital General de Guamúchil se encuentra en espera "
        "del anteproyecto para que pueda ingresar a Hacienda.\n"
        "Impermeabilización de 10 unidades médicas: ya existe contrato, pero no "
        "se ha iniciado por falta de anticipo.",
        Estatus.EN_PROCESO, "En espera.",
        "Seguimiento con los enlaces de las respectivas unidades.",
        "Unidad de Infraestructura.", None,
    ),
    (
        "sonora", "Recursos Humanos",
        "62 plazas de enfermería vacantes en el norte del estado.\n"
        "Rotación alta en turnos nocturnos: 18 renuncias en el último trimestre.",
        Estatus.EN_PROCESO, "Convocatoria publicada, en proceso de evaluación.",
        "Convocatoria estatal abierta y mesa de trabajo con la representación sindical.",
        "Coordinación de Recursos Humanos.", dt.date(2026, 6, 15),
    ),
    (
        "sonora", "Logística",
        "3 de 7 rutas de distribución de medicamento sin unidad asignada.\n"
        "Retrasos de hasta 12 días en la entrega a unidades de la sierra.",
        Estatus.ABIERTA, "Sin avance.",
        "Solicitud de arrendamiento de unidades ante Recursos Materiales.",
        "Coordinación de Recursos Materiales.", dt.date(2026, 7, 1),
    ),
    # ---------------- Sureste ----------------
    (
        "chiapas", "Abasto",
        "412 claves en cero en unidades de primer nivel.\n"
        "Desabasto de antirretrovirales en 4 hospitales.\n"
        "Material de curación con surtimiento parcial desde mayo.",
        Estatus.EN_PROCESO, "Surtimiento parcial en proceso.",
        "Mesa semanal con el almacén estatal y seguimiento a oficios de compra.",
        "Coordinación de Recursos Materiales.", dt.date(2026, 5, 4),
    ),
    (
        "chiapas", "Infraestructura",
        "Hospital Comunitario de Ocosingo: falla en la subestación eléctrica, "
        "opera con planta de emergencia desde hace 3 semanas.\n"
        "Centro de Salud Tila: filtraciones en área de urgencias.",
        Estatus.ABIERTA, "En espera de dictamen técnico.",
        "Levantamiento técnico solicitado a la Unidad de Infraestructura.",
        "Unidad de Infraestructura.", dt.date(2026, 8, 3),
    ),
    (
        "chiapas", "Seguridad",
        "2 unidades médicas en zona de conflicto con acceso restringido.\n"
        "Personal solicita acompañamiento para traslados nocturnos.",
        Estatus.EN_PROCESO, "Coordinación con autoridades estatales en curso.",
        "Mesa de seguridad con la Secretaría de Seguridad Pública estatal.",
        "Dirección General.", dt.date(2026, 7, 20),
    ),
    (
        "oaxaca", "Recursos Humanos",
        "Retén de pagos a 140 trabajadores eventuales por inconsistencias en el "
        "padrón.\n"
        "24 plazas de médico general sin cubrir en la región Mixteca.",
        Estatus.EN_PROCESO, "Depuración del padrón al 60%.",
        "Cotejo de expedientes con nómina central.",
        "Coordinación de Recursos Humanos.", dt.date(2026, 6, 1),
    ),
    (
        "oaxaca", "Servicios Generales",
        "Contrato de recolección de RPBI vencido en 9 unidades.\n"
        "Acumulación de residuos en 2 hospitales por encima de la capacidad.",
        Estatus.ABIERTA, "Urgente. Riesgo sanitario.",
        "Contratación directa en trámite ante Recursos Materiales.",
        "Coordinación de Recursos Materiales.", dt.date(2026, 8, 25),
    ),
    (
        "yucatan", "Infraestructura",
        "Ampliación del área de urgencias del Hospital General: obra detenida "
        "al 70% por falta de ministración.",
        Estatus.EN_PROCESO, "Obra detenida, expediente completo.",
        "Seguimiento a la solicitud de ministración ante Finanzas.",
        "Unidad de Infraestructura.", dt.date(2026, 4, 10),
    ),
    # ---------------- Centro ----------------
    (
        "ciudad-de-mexico", "Abasto",
        "Desabasto de 38 claves de alta rotación en 12 centros de salud.\n"
        "Retraso en la entrega del proveedor adjudicado en la licitación 2026.",
        Estatus.EN_PROCESO, "Surtimiento al 45%.",
        "Penalización al proveedor y compra emergente autorizada.",
        "Coordinación de Recursos Materiales.", dt.date(2026, 7, 8),
    ),
    (
        "ciudad-de-mexico", "Comunicación",
        "Fallas intermitentes del expediente clínico electrónico en 6 unidades.\n"
        "Enlace de datos insuficiente en 3 centros de salud.",
        Estatus.ABIERTA, "En diagnóstico.",
        "Levantamiento con el área de Tecnologías de la Información.",
        "Coordinación de Tecnologías de la Información.", dt.date(2026, 8, 30),
    ),
    (
        "hidalgo", "Pasivos",
        "Adeudo con 7 proveedores de servicios de laboratorio por $42.3 mdp "
        "correspondiente a 2025.",
        Estatus.ABIERTA, "En espera de suficiencia presupuestal.",
        "Conciliación de saldos y envío de expediente a Finanzas.",
        "Coordinación de Finanzas.", dt.date(2025, 11, 1),
    ),
    # ---------------- Noreste ----------------
    (
        "veracruz", "Recursos Humanos",
        "210 plazas liberadas por jubilación sin reposición.\n"
        "Personal de intendencia insuficiente en 15 unidades.",
        Estatus.ABIERTA, "En espera de autorización de plazas.",
        "Gestión ante la Coordinación de RH y priorización de unidades.",
        "Coordinación de Recursos Humanos.", dt.date(2026, 3, 15),
    ),
    (
        "veracruz", "Servicios Generales",
        "Suministro de agua potable irregular en el Hospital Regional.\n"
        "Se contratan pipas de forma emergente 3 veces por semana.",
        Estatus.EN_PROCESO, "Solución temporal en operación.",
        "Proyecto de pozo propio en evaluación técnica.",
        "Unidad de Infraestructura.", dt.date(2026, 5, 20),
    ),
    (
        "tamaulipas", "Logística",
        "Cadena de frío comprometida: 4 refrigeradores de biológicos fuera de "
        "servicio en la zona centro.",
        Estatus.EN_PROCESO, "2 equipos ya reemplazados, faltan 2.",
        "Compra emergente de equipos y resguardo temporal en unidad vecina.",
        "Coordinación de Recursos Materiales.", dt.date(2026, 8, 12),
    ),
    # ---------------- Suroeste ----------------
    (
        "guerrero", "Infraestructura",
        "Daños por lluvias en 6 unidades médicas de la región Costa Chica.\n"
        "2 unidades operando parcialmente.",
        Estatus.EN_PROCESO, "Evaluación de daños concluida.",
        "Gestión de recursos para rehabilitación ante la Unidad de Infraestructura.",
        "Unidad de Infraestructura.", dt.date(2026, 9, 2),
    ),
    (
        "guerrero", "Abasto",
        "Desabasto de soluciones intravenosas en 9 unidades.\n"
        "Caducidad próxima de 1,200 piezas en almacén estatal.",
        Estatus.ABIERTA, "Sin avance.",
        "Solicitud de redistribución entre entidades de la región.",
        "Coordinación de Recursos Materiales.", dt.date(2026, 8, 18),
    ),
    (
        "michoacan", "Seguridad",
        "3 unidades médicas con reporte de incidentes de violencia en el perimetro.\n"
        "Personal solicita medidas de protección.",
        Estatus.EN_PROCESO, "Mesa de seguridad instalada.",
        "Coordinación con autoridades municipales y estatales.",
        "Dirección General.", dt.date(2026, 7, 5),
    ),
    (
        "puebla", "Recursos Humanos",
        "Pago pendiente de guardias extraordinarias a 87 trabajadores.",
        Estatus.CERRADA, "Resuelto: pago dispersado el 5 de septiembre.",
        "Se aplicó el pago retroactivo en la nómina de septiembre.",
        "Coordinación de Recursos Humanos.", dt.date(2026, 6, 28),
    ),
]


class Command(BaseCommand):
    help = "Crea situaciones de ejemplo (DATOS FICTICIOS) para mostrar la aplicacion."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Borra TODAS las situaciones existentes antes de sembrar.",
        )

    @transaction.atomic
    def handle(self, *args, **opciones):
        if opciones["limpiar"]:
            BitacoraSituacion.objects.all().delete()
            borradas = Situacion.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f"Borradas {borradas} situaciones."))
        elif Situacion.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    "Ya hay situaciones registradas. Usa --limpiar si quieres "
                    "reemplazarlas por los ejemplos."
                )
            )
            return

        autor = (
            Usuario.objects.filter(rol="SUPER_ADMIN").first()
            or Usuario.objects.first()
        )

        categorias = {
            nombre: Categoria.objects.get_or_create(
                nombre_normalizado=nombre.lower()
                .replace("í", "i").replace("ó", "o").replace("á", "a"),
                defaults={"nombre": nombre, "creada_por": autor},
            )[0]
            for nombre in CATEGORIAS + ["Comunicación"]
        }

        creadas, sin_entidad = 0, set()
        ordenes: dict[int, int] = {}

        for (clave, categoria, tema, estatus, detalle,
             acciones, responsable, inicio) in EJEMPLOS:
            entidad = Entidad.objects.filter(clave=clave).first()
            if entidad is None:
                sin_entidad.add(clave)
                continue

            archivada = estatus == Estatus.CERRADA
            if archivada:
                orden = None
            else:
                ordenes[entidad.pk] = ordenes.get(entidad.pk, 0) + 1
                orden = ordenes[entidad.pk]

            situacion = Situacion.objects.create(
                entidad=entidad,
                categoria=categorias[categoria],
                tema=tema,
                fecha_inicio=inicio,
                estatus=estatus,
                estatus_detalle=detalle,
                acciones=acciones,
                responsable=responsable,
                fecha_estimada_solucion=None,
                orden=orden,
                archivada_en=dt.datetime(2026, 9, 5, 12, 0, tzinfo=dt.timezone.utc)
                if archivada else None,
                creada_por=autor,
                actualizada_por=autor,
            )
            BitacoraSituacion.objects.create(
                situacion=situacion, usuario=autor, accion="CREACION"
            )
            creadas += 1

        if sin_entidad:
            self.stdout.write(
                self.style.WARNING(f"Entidades no encontradas: {', '.join(sin_entidad)}")
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"{creadas} situaciones de ejemplo creadas en "
                f"{len(ordenes)} entidades. DATOS FICTICIOS."
            )
        )
