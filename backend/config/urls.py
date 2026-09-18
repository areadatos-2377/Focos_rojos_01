from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def salud(_request):
    """Sonda de salud para Docker y Railway."""
    return JsonResponse({"estado": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/salud/", salud, name="salud"),
    path("api/", include("usuarios.urls")),
    path("api/", include("catalogos.urls")),
    path("api/", include("situaciones.urls")),
]
