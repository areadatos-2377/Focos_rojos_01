"""Mixin de alcance por entidad para ViewSets.

Al filtrar en `get_queryset()` la restriccion cubre a la vez list, retrieve, update
y las @action. Un objeto fuera de alcance responde 404 (no 403): no se filtra la
existencia de datos ajenos.
"""
from core.scoping import entidades_visibles


class AlcanceEntidadMixin:
    #: Ruta al FK hacia Entidad desde el modelo del viewset.
    #: `None` significa que el propio modelo ES Entidad.
    lookup_entidad = "entidad"

    def get_queryset(self):
        qs = super().get_queryset()
        visibles = entidades_visibles(self.request.user)
        if self.lookup_entidad is None:
            return qs.filter(pk__in=visibles.values("pk"))
        return qs.filter(**{f"{self.lookup_entidad}__in": visibles})
