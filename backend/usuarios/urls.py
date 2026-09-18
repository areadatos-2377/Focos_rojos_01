from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AccesosView,
    CambiarPasswordView,
    LoginView,
    LogoutView,
    UsuarioViewSet,
    YoView,
)

router = DefaultRouter()
router.register("usuarios", UsuarioViewSet, basename="usuario")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/yo/", YoView.as_view(), name="yo"),
    path("auth/cambiar-password/", CambiarPasswordView.as_view(), name="cambiar-password"),
    path("auditoria/accesos/", AccesosView.as_view(), name="accesos"),
    *router.urls,
]
