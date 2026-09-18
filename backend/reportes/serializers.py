from rest_framework import serializers

from core.fields import EntidadPermitidaField

from .plantilla import MAX_SITUACIONES


class GenerarReporteSerializer(serializers.Serializer):
    """Los 4 datos de portada mas la seleccion de situaciones.

    El orden de `situaciones` es el que decide cual sale como SITUACION 1, 2, 3...
    """

    entidad = EntidadPermitidaField()
    fecha_entrega = serializers.DateField()
    responsable_reporte = serializers.CharField(max_length=200)
    fecha_corte = serializers.DateField()
    situaciones = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        max_length=MAX_SITUACIONES,
        help_text=f"Hasta {MAX_SITUACIONES} identificadores, en el orden deseado.",
    )
    formato = serializers.ChoiceField(choices=["pdf", "docx"], default="pdf")

    def validate_responsable_reporte(self, valor):
        limpio = " ".join(valor.split())
        if len(limpio) < 3:
            raise serializers.ValidationError(
                "Indica quien llena el reporte (al menos 3 caracteres)."
            )
        return limpio

    def validate(self, attrs):
        if attrs["fecha_entrega"] < attrs["fecha_corte"]:
            raise serializers.ValidationError(
                {
                    "fecha_entrega": "La fecha de entrega no puede ser anterior a la "
                    "fecha de corte."
                }
            )
        return attrs
