from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mixins import AlcanceEntidadMixin
from core.scoping import entidades_visibles

from . import services
from .models import Situacion
from .serializers import (
    BitacoraSerializer,
    ReabrirSerializer,
    ReordenarSerializer,
    SituacionSerializer,
)


class SituacionViewSet(AlcanceEntidadMixin, viewsets.ModelViewSet):
    """Situaciones del alcance del usuario.

    Por omision la galeria muestra solo las activas; las cerradas se consultan
    explicitamente con `?archivadas=true`.
    """

    serializer_class = SituacionSerializer
    queryset = Situacion.objects.select_related(
        "entidad", "entidad__region", "categoria", "creada_por", "actualizada_por"
    )
    lookup_entidad = "entidad"
    filterset_fields = ["entidad", "estatus", "categoria"]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()

        parametros = self.request.query_params

        entidad_clave = parametros.get("entidad_clave")
        if entidad_clave:
            qs = qs.filter(entidad__clave=entidad_clave)

        # Filtros de la vista de tabla (solo utiles con alcance nacional).
        region = parametros.get("region")
        if region:
            qs = qs.filter(entidad__region__clave=region)

        orden = parametros.get("orden")
        if orden:
            qs = qs.filter(orden=orden)

        if self.action == "list":
            archivadas = parametros.get("archivadas", "").lower()
            qs = qs.archivadas() if archivadas in ("1", "true", "si") else qs.activas()

        busqueda = parametros.get("q")
        if busqueda:
            qs = qs.filter(
                Q(tema__icontains=busqueda) | Q(responsable__icontains=busqueda)
            )

        return qs

    def perform_create(self, serializer):
        serializer.instance = services.crear_situacion(
            usuario=self.request.user, **serializer.validated_data
        )

    def perform_update(self, serializer):
        serializer.instance = services.actualizar_situacion(
            serializer.instance, usuario=self.request.user, **serializer.validated_data
        )

    @action(detail=True, methods=["post"])
    def cerrar(self, request, pk=None):
        situacion = services.cerrar_situacion(self.get_object(), usuario=request.user)
        return Response(self.get_serializer(situacion).data)

    @action(detail=True, methods=["post"])
    def reabrir(self, request, pk=None):
        entrada = ReabrirSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        situacion = services.reabrir_situacion(
            self.get_object(),
            usuario=request.user,
            estatus=entrada.validated_data["estatus"],
        )
        return Response(self.get_serializer(situacion).data)

    @action(detail=True, methods=["get"])
    def bitacora(self, request, pk=None):
        """Historial de la situacion. Lo ve cualquiera que pueda ver la situacion."""
        situacion = self.get_object()
        movimientos = situacion.bitacora.select_related("usuario")
        return Response(BitacoraSerializer(movimientos, many=True).data)


class OrdenSituacionesView(APIView):
    """Reordena las situaciones activas de una entidad.

    Se exige la lista COMPLETA de activas: una lista parcial significa que quien la
    envio tenia una vista desactualizada.
    """

    def put(self, request, clave):
        entidad = get_object_or_404(entidades_visibles(request.user), clave=clave)

        entrada = ReordenarSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        try:
            situaciones = services.reordenar_situaciones(
                entidad, entrada.validated_data["orden"]
            )
        except services.OrdenInvalido as error:
            return Response({"detalle": str(error)}, status=status.HTTP_409_CONFLICT)

        return Response(SituacionSerializer(situaciones, many=True).data)
