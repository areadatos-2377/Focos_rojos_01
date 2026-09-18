from django.urls import path

from .views import VistaPreviaReporteView

urlpatterns = [
    path(
        "reportes/vista-previa/",
        VistaPreviaReporteView.as_view(),
        name="reporte-vista-previa",
    ),
]
