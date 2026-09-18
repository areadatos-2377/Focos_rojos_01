"""Situaciones de ejemplo para mostrar la aplicacion con contenido realista.

El estilo y las categorias vienen de `legacy/Formato_Focos_Rojos_Gira_ejemplo.docx`:
el "tema" enumera varios puntos con cifras, la fecha de inicio suele venir vacia y el
responsable es un area, no una persona.

Las cinco situaciones de Sinaloa son las del documento real, textuales. El resto se
componen a partir de arquetipos por categoria, variando cifras, meses y unidades con
una semilla derivada de la entidad: el resultado es distinto en cada estado pero
reproducible entre ejecuciones.

DATOS FICTICIOS. `--limpiar` borra todas las situaciones existentes.
"""
import datetime as dt
import random

from django.core.management.base import BaseCommand
from django.db import transaction

from catalogos.models import Categoria, Entidad
from situaciones.models import BitacoraSituacion, Estatus, Situacion
from usuarios.models import Usuario

CATEGORIAS = [
    "Recursos Humanos", "Abasto", "Servicios Generales", "Pasivos",
    "Infraestructura", "Logística", "Seguridad", "Comunicación",
]

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre",
]

UNIDADES = [
    "Hospital General", "Hospital Rural No. 42", "Hospital Comunitario",
    "Centro de Salud con Servicios Ampliados", "Hospital Integral",
    "Centro de Salud urbano", "Hospital de la Mujer",
]

# Las cinco situaciones reales del documento de ejemplo, textuales.
SINALOA = [
    (
        "Recursos Humanos",
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
        "Abasto",
        "Claves totales 1503, de las cuales 724 se encuentran en 0.\n"
        "328 claves prioritarias que no tenemos en unidades de salud.\n"
        "Desabasto de 15 claves oncológicas en HGC, HPS e ISCAN.\n"
        "Material de curación fuera de cuadro básico.",
        Estatus.EN_PROCESO, "En espera de surtimiento.",
        "Seguimiento a oficios de solicitud de surtimiento.",
        "Coordinación de Recursos Materiales.", None,
    ),
    (
        "Servicios Generales",
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
        "Pasivos",
        "Pagos pendientes 2025 a 2 proveedores por $759,777.55:\n"
        "Servicios Generales $398,230.36 y Servicios Médicos Integrales $361,547.19.\n"
        "Pagos pendientes 2026 a 13 proveedores por $125.5 mdp:\n"
        "Servicios Generales $5.5 mdp y Servicios Médicos Integrales $120 mdp.",
        Estatus.ABIERTA, "En espera.",
        "Seguimiento a oficios de solicitudes de pago ante la Coordinación de Finanzas.",
        "Coordinación de Finanzas.", None,
    ),
    (
        "Infraestructura",
        "La sustitución del Hospital General de Guamúchil se encuentra en espera "
        "del anteproyecto para que pueda ingresar a Hacienda.\n"
        "Impermeabilización de 10 unidades médicas: ya existe contrato, pero no "
        "se ha iniciado por falta de anticipo.",
        Estatus.EN_PROCESO, "En espera.",
        "Seguimiento con los enlaces de las respectivas unidades.",
        "Unidad de Infraestructura.", None,
    ),
]

# (categoria, tema, detalle, acciones, responsable)
# Marcadores: cada uno tiene su propio rango realista. No son intercambiables:
#   {plazas} {personas} {unidades} {pct} {semanas} {dias} {proveedores}
#   {claves_total} {claves_cero} {claves_prio} {piezas} {equipos} {incidentes}
#   {rutas_sin} {rutas_total} {monto} {monto2} {unidad} {mes} {mes2} {entidad}
ARQUETIPOS = [
    (
        "Recursos Humanos",
        "Liberación de {plazas} plazas por jubilaciones, renuncias y defunciones sin "
        "reposición.\n"
        "{personas} trabajadores pendientes de reincorporarse a su plaza de base.\n"
        "{personas} jefaturas de la Estructura Estatal pendientes por contratar.",
        "En espera de autorización de plazas.",
        "Gestiones ante la Coordinación de Recursos Humanos.",
        "Coordinación de Recursos Humanos.",
    ),
    (
        "Recursos Humanos",
        "{plazas} plazas de enfermería vacantes, concentradas en turnos nocturnos y "
        "fines de semana.\n"
        "{personas} renuncias en el último trimestre.\n"
        "Cobertura incompleta en {unidades} unidades de primer nivel.",
        "Convocatoria publicada, en proceso de evaluación.",
        "Convocatoria estatal abierta y mesa de trabajo con la representación sindical.",
        "Coordinación de Recursos Humanos.",
    ),
    (
        "Recursos Humanos",
        "Pago pendiente de guardias extraordinarias a {personas} trabajadores "
        "correspondientes a {mes}.\n"
        "Inconsistencias en el padrón de {personas} eventuales.",
        "Depuración del padrón en proceso.",
        "Cotejo de expedientes con nómina central.",
        "Coordinación de Recursos Humanos.",
    ),
    (
        "Abasto",
        "Claves totales {claves_total}, de las cuales {claves_cero} se encuentran en cero.\n"
        "{claves_prio} claves prioritarias sin existencia en unidades de primer nivel.\n"
        "Material de curación con surtimiento parcial desde {mes}.",
        "Surtimiento parcial en proceso.",
        "Mesa semanal con el almacén estatal y seguimiento a oficios de compra.",
        "Coordinación de Recursos Materiales.",
    ),
    (
        "Abasto",
        "Desabasto de {claves_prio} claves oncológicas en el {unidad}.\n"
        "Retraso del proveedor adjudicado en la licitación 2026.\n"
        "Caducidad próxima de {piezas} piezas en almacén estatal.",
        "Surtimiento al {pct}%.",
        "Penalización al proveedor y compra emergente autorizada.",
        "Coordinación de Recursos Materiales.",
    ),
    (
        "Abasto",
        "Desabasto de soluciones intravenosas y antibióticos de primera línea "
        "en {unidades} unidades.\n"
        "Sin existencia de {claves_prio} claves de alta rotación.",
        "Sin avance.",
        "Solicitud de redistribución entre entidades de la región.",
        "Coordinación de Recursos Materiales.",
    ),
    (
        "Servicios Generales",
        "Servicio de Gas LP en riesgo de suspensión por falta de pago de {mes} y "
        "{mes2} de 2026.\n"
        "Diésel para plantas de emergencia con suministro irregular en {unidades} unidades.\n"
        "Suficiencias presupuestarias no autorizadas.",
        "En espera.",
        "Seguimiento a oficios de solicitudes de pago a la Coordinación de Finanzas.",
        "Coordinación de Finanzas.",
    ),
    (
        "Servicios Generales",
        "Contrato de recolección de RPBI vencido en {unidades} unidades.\n"
        "Acumulación de residuos por encima de la capacidad en el {unidad}.",
        "Urgente. Riesgo sanitario.",
        "Contratación directa en trámite ante Recursos Materiales.",
        "Coordinación de Recursos Materiales.",
    ),
    (
        "Servicios Generales",
        "Suministro de agua potable irregular en el {unidad}.\n"
        "Se contratan pipas de forma emergente {veces} veces por semana desde {mes}.",
        "Solución temporal en operación.",
        "Proyecto de pozo propio en evaluación técnica.",
        "Unidad de Infraestructura.",
    ),
    (
        "Pasivos",
        "Pagos pendientes 2025 a {proveedores} proveedores por ${monto} mdp.\n"
        "Pagos pendientes 2026 a {proveedores} proveedores por ${monto2} mdp, concentrados en "
        "servicios médicos integrales y servicios generales.",
        "En espera de suficiencia presupuestal.",
        "Conciliación de saldos y envío de expediente a Finanzas.",
        "Coordinación de Finanzas.",
    ),
    (
        "Pasivos",
        "Adeudo con {proveedores} proveedores de servicios de laboratorio y gabinete por "
        "${monto} mdp correspondiente al ejercicio 2025.",
        "En espera.",
        "Seguimiento a oficios de solicitudes de pago ante la Coordinación de Finanzas.",
        "Coordinación de Finanzas.",
    ),
    (
        "Infraestructura",
        "Sustitución del {unidad} en espera del anteproyecto para ingresar a Hacienda.\n"
        "Impermeabilización de {unidades} unidades médicas: existe contrato, pero no "
        "inicia por falta de anticipo.",
        "En espera de dictamen técnico.",
        "Seguimiento con los enlaces de las respectivas unidades.",
        "Unidad de Infraestructura.",
    ),
    (
        "Infraestructura",
        "Falla en la subestación eléctrica del {unidad}: opera con planta de "
        "emergencia desde hace {semanas} semanas.\n"
        "Filtraciones en área de urgencias en {unidades} unidades.",
        "En espera de dictamen técnico.",
        "Levantamiento técnico solicitado a la Unidad de Infraestructura.",
        "Unidad de Infraestructura.",
    ),
    (
        "Infraestructura",
        "Ampliación del área de urgencias del {unidad}: obra detenida al {pct}% "
        "por falta de ministración.\n"
        "Daños por lluvias en {unidades} unidades médicas.",
        "Obra detenida, expediente completo.",
        "Gestión de recursos para rehabilitación ante la Unidad de Infraestructura.",
        "Unidad de Infraestructura.",
    ),
    (
        "Logística",
        "{rutas_sin} de {rutas_total} rutas de distribución de medicamento sin unidad asignada.\n"
        "Retrasos de hasta {dias} días en la entrega a unidades alejadas.",
        "Sin avance.",
        "Solicitud de arrendamiento de unidades ante Recursos Materiales.",
        "Coordinación de Recursos Materiales.",
    ),
    (
        "Logística",
        "Cadena de frío comprometida: {equipos} refrigeradores de biológicos fuera "
        "de servicio.\n"
        "Resguardo temporal en unidades vecinas desde {mes}.",
        "Reemplazo parcial en proceso.",
        "Compra emergente de equipos y resguardo temporal en unidad vecina.",
        "Coordinación de Recursos Materiales.",
    ),
    (
        "Seguridad",
        "{unidades} unidades médicas en zona de acceso restringido.\n"
        "El personal solicita acompañamiento para traslados nocturnos.",
        "Coordinación con autoridades estatales en curso.",
        "Mesa de seguridad con la Secretaría de Seguridad Pública estatal.",
        "Dirección General.",
    ),
    (
        "Seguridad",
        "Reporte de {incidentes} incidentes de violencia en el perímetro de unidades "
        "médicas durante {mes}.\n"
        "Solicitud de medidas de protección para el personal de guardia.",
        "Mesa de seguridad instalada.",
        "Coordinación con autoridades municipales y estatales.",
        "Dirección General.",
    ),
    (
        "Comunicación",
        "Fallas intermitentes del expediente clínico electrónico en {unidades} unidades.\n"
        "Enlace de datos insuficiente en {unidades} centros de salud.",
        "En diagnóstico.",
        "Levantamiento con el área de Tecnologías de la Información.",
        "Coordinación de Tecnologías de la Información.",
    ),
    (
        "Comunicación",
        "{unidades} unidades sin telefonía ni radiocomunicación operativa.\n"
        "Dificultad para coordinar traslados de urgencia en zonas sin cobertura.",
        "En espera de contrato de servicio.",
        "Solicitud de servicio satelital para unidades sin cobertura.",
        "Coordinación de Tecnologías de la Información.",
    ),
]

RESUELTAS = [
    (
        "Recursos Humanos",
        "Pago pendiente de guardias extraordinarias a {personas} trabajadores.",
        "Resuelto: el pago se dispersó en la nómina de septiembre.",
        "Se aplicó el pago retroactivo en la nómina de septiembre.",
        "Coordinación de Recursos Humanos.",
    ),
    (
        "Abasto",
        "Desabasto de {claves_prio} claves de material de curación en {unidades} unidades.",
        "Resuelto: surtimiento completo confirmado por el almacén estatal.",
        "Compra emergente autorizada y entregada.",
        "Coordinación de Recursos Materiales.",
    ),
    (
        "Servicios Generales",
        "Suspensión del servicio de lavandería en el {unidad} por falta de pago.",
        "Resuelto: contrato regularizado.",
        "Pago liberado por la Coordinación de Finanzas.",
        "Coordinación de Finanzas.",
    ),
]


def _rellenar(plantilla: str, azar: random.Random, entidad_nombre: str) -> str:
    claves_total = azar.randint(900, 1600)
    return plantilla.format(
        plazas=azar.randint(35, 520),
        personas=azar.randint(6, 180),
        unidades=azar.randint(2, 14),
        pct=azar.choice([25, 35, 45, 55, 60, 70, 80]),
        semanas=azar.randint(2, 8),
        dias=azar.randint(4, 15),
        veces=azar.randint(2, 5),
        proveedores=azar.randint(2, 16),
        claves_total=claves_total,
        claves_cero=azar.randint(180, claves_total // 2),
        claves_prio=azar.randint(8, 120),
        piezas=azar.randint(300, 2500),
        equipos=azar.randint(2, 9),
        incidentes=azar.randint(2, 9),
        rutas_sin=azar.randint(2, 4),
        rutas_total=azar.randint(6, 12),
        monto=azar.choice(["12.4", "28.7", "42.3", "59.8", "125.5"]),
        monto2=azar.choice(["5.5", "18.2", "34.6", "76.1", "120"]),
        unidad=azar.choice(UNIDADES),
        mes=azar.choice(MESES),
        mes2=azar.choice(MESES),
        entidad=entidad_nombre,
    )


class Command(BaseCommand):
    help = "Crea situaciones de ejemplo (DATOS FICTICIOS) en todas las entidades."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpiar", action="store_true",
            help="Borra TODAS las situaciones existentes antes de sembrar.",
        )
        parser.add_argument(
            "--por-entidad", type=int, default=5,
            help="Situaciones activas por entidad (por omision 5, el tope del formato).",
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
                    "Ya hay situaciones registradas. Usa --limpiar para reemplazarlas."
                )
            )
            return

        autor = Usuario.objects.filter(rol="SUPER_ADMIN").first() or Usuario.objects.first()
        categorias = self._asegurar_categorias(autor)

        por_entidad = max(1, min(opciones["por_entidad"], 5))
        creadas = 0
        archivadas = 0

        for entidad in Entidad.objects.select_related("region").order_by("nombre"):
            # Semilla derivada del nombre: cada entidad recibe una combinacion propia
            # y estable entre ejecuciones.
            azar = random.Random(f"focos-{entidad.clave}")

            if entidad.clave == "sinaloa":
                bloques = [
                    (cat, tema, est, det, acc, resp, ini)
                    for cat, tema, est, det, acc, resp, ini in SINALOA
                ]
            else:
                bloques = self._componer(azar, entidad, por_entidad)

            for orden, (cat, tema, estatus, detalle, acciones, resp, inicio) in enumerate(
                bloques[:por_entidad], start=1
            ):
                self._crear(
                    entidad, categorias[cat], tema, estatus, detalle, acciones,
                    resp, inicio, orden, autor,
                )
                creadas += 1

            # Una de cada tres entidades arrastra ademas una situacion ya resuelta,
            # para que la vista de archivadas tenga contenido.
            if azar.random() < 0.34:
                cat, tema, detalle, acciones, resp = azar.choice(RESUELTAS)
                self._crear(
                    entidad, categorias[cat],
                    _rellenar(tema, azar, entidad.nombre),
                    Estatus.CERRADA, detalle, acciones, resp,
                    dt.date(2026, azar.randint(3, 7), azar.randint(1, 28)),
                    None, autor,
                    archivada_en=dt.datetime(
                        2026, 9, azar.randint(1, 10), 12, 0, tzinfo=dt.timezone.utc
                    ),
                )
                creadas += 1
                archivadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{creadas} situaciones creadas en {Entidad.objects.count()} entidades "
                f"({archivadas} archivadas). DATOS FICTICIOS."
            )
        )

    def _asegurar_categorias(self, autor) -> dict:
        from catalogos.normalizacion import normalizar_nombre

        catalogo = {}
        for nombre in CATEGORIAS:
            catalogo[nombre] = Categoria.objects.get_or_create(
                nombre_normalizado=normalizar_nombre(nombre),
                defaults={"nombre": nombre, "creada_por": autor},
            )[0]
        return catalogo

    def _componer(self, azar, entidad, cuantas) -> list:
        """Elige arquetipos de categorias distintas y los rellena para esta entidad."""
        elegidos = []
        categorias_usadas = set()
        candidatos = ARQUETIPOS[:]
        azar.shuffle(candidatos)

        for cat, tema, detalle, acciones, resp in candidatos:
            if len(elegidos) >= cuantas:
                break
            if cat in categorias_usadas:
                continue
            categorias_usadas.add(cat)
            elegidos.append((
                cat,
                _rellenar(tema, azar, entidad.nombre),
                azar.choice([Estatus.ABIERTA, Estatus.EN_PROCESO, Estatus.ABIERTA]),
                _rellenar(detalle, azar, entidad.nombre),
                acciones,
                resp,
                # La fecha de inicio casi siempre viene vacia, como en el formato real.
                dt.date(2026, azar.randint(2, 8), azar.randint(1, 28))
                if azar.random() < 0.4 else None,
            ))
        return elegidos

    def _crear(self, entidad, categoria, tema, estatus, detalle, acciones,
               responsable, inicio, orden, autor, archivada_en=None):
        situacion = Situacion.objects.create(
            entidad=entidad,
            categoria=categoria,
            tema=tema,
            fecha_inicio=inicio,
            estatus=estatus,
            estatus_detalle=detalle,
            acciones=acciones,
            responsable=responsable,
            fecha_estimada_solucion=None,
            orden=orden,
            archivada_en=archivada_en,
            creada_por=autor,
            actualizada_por=autor,
        )
        BitacoraSituacion.objects.create(
            situacion=situacion, usuario=autor, accion="CREACION"
        )
        return situacion
