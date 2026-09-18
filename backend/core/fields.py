"""Campos de serializer que aplican el alcance por region en ESCRITURA.

Con esto, enviar una entidad fuera de alcance produce un error de validacion de DRF
sin que la vista tenga que comprobar el rol.
"""
from rest_framework import serializers

from core.scoping import entidades_visibles


class EntidadPermitidaField(serializers.SlugRelatedField):
    def __init__(self, **kwargs):
        kwargs.setdefault("slug_field", "clave")
        super().__init__(**kwargs)

    def get_queryset(self):
        return entidades_visibles(self.context["request"].user)
