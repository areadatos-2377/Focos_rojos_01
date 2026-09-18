from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import OrdenSituacionesView, SituacionViewSet

router = DefaultRouter()
router.register("situaciones", SituacionViewSet, basename="situacion")

urlpatterns = [
    path(
        "entidades/<slug:clave>/orden-situaciones/",
        OrdenSituacionesView.as_view(),
        name="orden-situaciones",
    ),
    *router.urls,
]
