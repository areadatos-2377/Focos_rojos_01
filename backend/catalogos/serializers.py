from rest_framework import serializers

from .models import Categoria, Entidad, Region
from .normalizacion import normalizar_nombre


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ("id", "clave", "nombre", "orden")


class EntidadSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)

    class Meta:
        model = Entidad
        fields = ("id", "clave", "nombre", "region", "activa")


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ("id", "nombre", "creada_en", "activa")
        read_only_fields = ("creada_en", "activa")

    def validate_nombre(self, valor):
        limpio = " ".join(valor.split())
        if len(limpio) < 3:
            raise serializers.ValidationError(
                "El nombre de la categoria debe tener al menos 3 caracteres."
            )
        if not normalizar_nombre(limpio):
            raise serializers.ValidationError("El nombre de la categoria no es valido.")
        return limpio


class FusionarCategoriaSerializer(serializers.Serializer):
    destino = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.filter(activa=True)
    )

    def validate_destino(self, destino):
        if destino.pk == self.context["categoria_origen"].pk:
            raise serializers.ValidationError("El destino no puede ser la misma categoria.")
        return destino
