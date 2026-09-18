from django.db import transaction
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.mixins import AlcanceEntidadMixin
from core.permissions import EsSuperAdmin, SoloLecturaOSuperAdmin
from core.scoping import entidades_visibles

from .models import Categoria, Entidad, Region
from .normalizacion import normalizar_nombre
from .serializers import (
    CategoriaSerializer,
    EntidadSerializer,
    FusionarCategoriaSerializer,
    RegionSerializer,
)


class RegionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Regiones visibles. Un regional recibe unicamente la suya."""

    serializer_class = RegionSerializer
    pagination_class = None

    def get_queryset(self):
        visibles = entidades_visibles(self.request.user)
        return Region.objects.filter(entidades__in=visibles).distinct()


class EntidadViewSet(AlcanceEntidadMixin, viewsets.ReadOnlyModelViewSet):
    """Entidades del alcance del usuario, identificadas por su clave (slug)."""

    serializer_class = EntidadSerializer
    queryset = Entidad.objects.select_related("region")
    lookup_field = "clave"
    lookup_entidad = None  # este viewset ES Entidad
    pagination_class = None


class CategoriaViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Catalogo global de categorias.

    Cualquier usuario autenticado puede listarlas y agregar una nueva. Renombrar,
    fusionar y eliminar queda reservado al super administrador.
    """

    serializer_class = CategoriaSerializer
    queryset = Categoria.objects.filter(activa=True)
    permission_classes = [SoloLecturaOSuperAdmin]
    pagination_class = None

    def create(self, request, *args, **kwargs):
        """Alta idempotente: si la categoria ya existe (ignorando mayusculas y
        acentos) se devuelve la existente con 200, no un error."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nombre = serializer.validated_data["nombre"]

        existente = Categoria.objects.filter(
            nombre_normalizado=normalizar_nombre(nombre)
        ).first()
        if existente is not None:
            if not existente.activa:
                existente.activa = True
                existente.save(update_fields=["activa"])
            return Response(self.get_serializer(existente).data, status=status.HTTP_200_OK)

        categoria = serializer.save(creada_por=request.user)
        return Response(
            self.get_serializer(categoria).data, status=status.HTTP_201_CREATED
        )

    def destroy(self, request, *args, **kwargs):
        categoria = self.get_object()
        if self._tiene_situaciones(categoria):
            return Response(
                {"detalle": "No se puede eliminar: hay situaciones que usan esta "
                            "categoria. Fusionala con otra en su lugar."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"], permission_classes=[EsSuperAdmin])
    def fusionar(self, request, pk=None):
        """Reasigna las situaciones de esta categoria a otra y desactiva la origen."""
        origen = self.get_object()
        serializer = FusionarCategoriaSerializer(
            data=request.data, context={"categoria_origen": origen}
        )
        serializer.is_valid(raise_exception=True)
        destino = serializer.validated_data["destino"]

        with transaction.atomic():
            movidas = self._reasignar_situaciones(origen, destino)
            origen.activa = False
            origen.save(update_fields=["activa"])

        return Response(
            {
                "detalle": f"Categoria fusionada en '{destino.nombre}'.",
                "situaciones_movidas": movidas,
                "destino": CategoriaSerializer(destino).data,
            }
        )

    @staticmethod
    def _tiene_situaciones(categoria) -> bool:
        try:
            from situaciones.models import Situacion
        except ImportError:
            return False
        return Situacion.objects.filter(categoria=categoria).exists()

    @staticmethod
    def _reasignar_situaciones(origen, destino) -> int:
        try:
            from situaciones.models import Situacion
        except ImportError:
            return 0
        return Situacion.objects.filter(categoria=origen).update(categoria=destino)
