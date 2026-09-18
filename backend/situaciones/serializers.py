from rest_framework import serializers

from catalogos.models import Categoria
from core.fields import EntidadPermitidaField

from .models import BitacoraSituacion, Situacion
from .services import CAMPOS_AUDITADOS


class SituacionSerializer(serializers.ModelSerializer):
    """La entidad se recibe por su clave y validada contra el alcance del usuario:
    mandar una entidad de otra region produce un error de validacion, no un 500."""

    entidad = EntidadPermitidaField()
    entidad_nombre = serializers.CharField(source="entidad.nombre", read_only=True)
    region_nombre = serializers.CharField(source="entidad.region.nombre", read_only=True)
    categoria = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.filter(activa=True)
    )
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)
    estatus_etiqueta = serializers.CharField(source="get_estatus_display", read_only=True)
    archivada = serializers.BooleanField(source="esta_archivada", read_only=True)
    creada_por_nombre = serializers.CharField(
        source="creada_por.nombre_completo", read_only=True, default=None
    )
    actualizada_por_nombre = serializers.CharField(
        source="actualizada_por.nombre_completo", read_only=True, default=None
    )

    class Meta:
        model = Situacion
        fields = (
            "id", "entidad", "entidad_nombre", "region_nombre",
            "categoria", "categoria_nombre",
            "tema", "fecha_inicio",
            "estatus", "estatus_etiqueta", "estatus_detalle",
            "acciones", "responsable", "fecha_estimada_solucion",
            "orden", "archivada", "archivada_en",
            "creada_por_nombre", "actualizada_por_nombre", "creada_en", "actualizada_en",
        )
        read_only_fields = (
            "orden", "archivada_en", "creada_en", "actualizada_en",
        )
        # DRF intenta construir un validador a partir de
        # `uniq_orden_entre_activas_por_entidad`, pero al ser un UniqueConstraint
        # CONDICIONAL necesita `archivada_en` entre los datos entrantes, y ese campo
        # es de solo lectura: en un PATCH revienta con KeyError.
        # El validador sobra: ni `orden` ni `archivada_en` los manda el cliente, los
        # gobierna `situaciones.services`, y la garantia real la da la base de datos.
        validators = []

    def validate(self, attrs):
        """La entidad se fija al crear y ya no se mueve: cambiarla obligaria a
        renumerar dos entidades a la vez."""
        if self.instance is not None and "entidad" in attrs:
            if attrs["entidad"].pk != self.instance.entidad_id:
                raise serializers.ValidationError(
                    {"entidad": "Una situacion no puede cambiar de entidad."}
                )
            attrs.pop("entidad")
        return attrs


class BitacoraSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    accion_etiqueta = serializers.CharField(source="get_accion_display", read_only=True)
    campo_etiqueta = serializers.SerializerMethodField()

    class Meta:
        model = BitacoraSituacion
        fields = (
            "id", "creado_en", "usuario_nombre",
            "accion", "accion_etiqueta",
            "campo", "campo_etiqueta", "valor_anterior", "valor_nuevo",
        )

    def get_usuario_nombre(self, movimiento):
        if movimiento.usuario is None:
            return "Usuario dado de baja"
        return movimiento.usuario.nombre_completo or movimiento.usuario.username

    def get_campo_etiqueta(self, movimiento):
        return CAMPOS_AUDITADOS.get(movimiento.campo, "")


class ReordenarSerializer(serializers.Serializer):
    orden = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class ReabrirSerializer(serializers.Serializer):
    estatus = serializers.ChoiceField(
        choices=[("ABIERTA", "Abierta"), ("EN_PROCESO", "En proceso")],
        default="EN_PROCESO",
    )
