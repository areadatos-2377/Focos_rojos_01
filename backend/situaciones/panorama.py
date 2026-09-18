"""Agregados para el panorama nacional.

Los conteos se calculan en la base de datos, no en el navegador: asi no dependen
de cuantos registros quepan en una pagina y no pueden quedar desfasados cuando
crezca el volumen.
"""
from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalogos.models import Categoria, Entidad
from core.permissions import EsAdministradorOSuperAdmin

from .models import Estatus, Situacion


class PanoramaView(APIView):
    """Vista de alcance nacional. Solo administradores."""

    permission_classes = [IsAuthenticated, EsAdministradorOSuperAdmin]

    def get(self, request):
        activas = Q(situaciones__archivada_en__isnull=True)

        entidades = (
            Entidad.objects.filter(activa=True)
            .select_related("region")
            .annotate(
                abiertas=Count(
                    "situaciones",
                    filter=activas & Q(situaciones__estatus=Estatus.ABIERTA),
                ),
                en_proceso=Count(
                    "situaciones",
                    filter=activas & Q(situaciones__estatus=Estatus.EN_PROCESO),
                ),
                archivadas=Count(
                    "situaciones", filter=Q(situaciones__archivada_en__isnull=False)
                ),
                activas_total=Count("situaciones", filter=activas),
            )
            .order_by("nombre")
        )

        matriz = (
            Situacion.objects.activas()
            .values("entidad__region__nombre", "categoria__nombre")
            .annotate(total=Count("id"))
        )

        totales = Situacion.objects.aggregate(
            activas=Count("id", filter=Q(archivada_en__isnull=True)),
            abiertas=Count("id", filter=Q(estatus=Estatus.ABIERTA, archivada_en__isnull=True)),
            en_proceso=Count(
                "id", filter=Q(estatus=Estatus.EN_PROCESO, archivada_en__isnull=True)
            ),
            archivadas=Count("id", filter=Q(archivada_en__isnull=False)),
        )

        return Response({
            "totales": {
                **totales,
                "entidades": entidades.count(),
                "entidades_con_situaciones": sum(
                    1 for e in entidades if e.activas_total > 0
                ),
            },
            "entidades": [
                {
                    "clave": e.clave,
                    "nombre": e.nombre,
                    "region": e.region.nombre,
                    "region_clave": e.region.clave,
                    "abiertas": e.abiertas,
                    "en_proceso": e.en_proceso,
                    "archivadas": e.archivadas,
                    "activas": e.activas_total,
                }
                for e in entidades
            ],
            "matriz": [
                {
                    "region": fila["entidad__region__nombre"],
                    "categoria": fila["categoria__nombre"],
                    "total": fila["total"],
                }
                for fila in matriz
            ],
            "categorias": list(
                Categoria.objects.filter(activa=True)
                .order_by("nombre")
                .values_list("nombre", flat=True)
            ),
        })
