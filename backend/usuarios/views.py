from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from core.permissions import EsAdministradorOSuperAdmin, EsSuperAdmin

from .models import RegistroAcceso, Usuario
from .serializers import (
    CambiarPasswordSerializer,
    LoginSerializer,
    PerfilSerializer,
    RegistroAccesoSerializer,
    UsuarioSerializer,
)
from .services import registrar_acceso


class LoginView(TokenObtainPairView):
    """Inicio de sesion. Deja constancia del acceso solo si las credenciales son validas."""

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        registrar_acceso(serializer.user, request)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Invalida el refresh token recibido."""

    def post(self, request):
        refresh = request.data.get("refresh")
        if not refresh:
            return Response(
                {"detalle": "Falta el token de refresco."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            return Response(
                {"detalle": "El token ya no es valido."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class YoView(APIView):
    """Perfil del usuario autenticado, con las entidades que puede ver."""

    def get(self, request):
        return Response(PerfilSerializer(request.user).data)


class CambiarPasswordView(APIView):
    def post(self, request):
        serializer = CambiarPasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["password_nueva"])
        request.user.save(update_fields=["password"])
        return Response({"detalle": "Contrasena actualizada."})


class UsuarioViewSet(viewsets.ModelViewSet):
    """Gestion de cuentas. Los administradores consultan; solo el super admin modifica."""

    serializer_class = UsuarioSerializer
    queryset = Usuario.objects.select_related("region").order_by("nombre_completo")

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated(), EsAdministradorOSuperAdmin()]
        return [IsAuthenticated(), EsSuperAdmin()]

    @action(detail=True, methods=["post"])
    def resetear_password(self, request, pk=None):
        """Asigna una contrasena temporal y la devuelve UNA sola vez."""
        import secrets
        import string

        usuario = self.get_object()
        alfabeto = string.ascii_letters + string.digits
        temporal = "".join(secrets.choice(alfabeto) for _ in range(12))
        usuario.set_password(temporal)
        usuario.save(update_fields=["password"])
        return Response(
            {
                "detalle": "Contrasena temporal generada. Anotala: no se vuelve a mostrar.",
                "password_temporal": temporal,
            }
        )


class AccesosView(ListAPIView):
    """Historial de inicios de sesion. Solo para administradores."""

    serializer_class = RegistroAccesoSerializer
    permission_classes = [IsAuthenticated, EsAdministradorOSuperAdmin]
    queryset = RegistroAcceso.objects.select_related("usuario")
    filterset_fields = ["usuario"]
