from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from catalogos.serializers import EntidadSerializer, RegionSerializer
from core.scoping import entidades_visibles

from .models import RegistroAcceso, Usuario


class PerfilSerializer(serializers.ModelSerializer):
    """Quien soy, que rol tengo y que entidades puedo tocar."""

    region = RegionSerializer(read_only=True)
    entidades = serializers.SerializerMethodField()
    rol_etiqueta = serializers.CharField(source="get_rol_display", read_only=True)

    class Meta:
        model = Usuario
        fields = (
            "id", "username", "nombre_completo", "email",
            "rol", "rol_etiqueta", "region", "entidades", "ultimo_acceso",
        )
        read_only_fields = fields

    def get_entidades(self, usuario):
        return EntidadSerializer(
            entidades_visibles(usuario).select_related("region"), many=True
        ).data


class LoginSerializer(TokenObtainPairSerializer):
    """Devuelve los tokens mas el perfil, y deja constancia del acceso."""

    def validate(self, attrs):
        datos = super().validate(attrs)
        datos["usuario"] = PerfilSerializer(self.user).data
        return datos


class UsuarioSerializer(serializers.ModelSerializer):
    """Alta y edicion de cuentas. Solo lo usa el super administrador."""

    password = serializers.CharField(write_only=True, required=False, min_length=8)
    region_nombre = serializers.CharField(source="region.nombre", read_only=True)
    rol_etiqueta = serializers.CharField(source="get_rol_display", read_only=True)

    class Meta:
        model = Usuario
        fields = (
            "id", "username", "nombre_completo", "email", "rol", "rol_etiqueta",
            "region", "region_nombre", "is_active", "ultimo_acceso", "password",
        )
        read_only_fields = ("ultimo_acceso",)

    def validate(self, attrs):
        from .models import Rol

        rol = attrs.get("rol", getattr(self.instance, "rol", None))
        region = attrs.get("region", getattr(self.instance, "region", None))
        if rol == Rol.REGIONAL and region is None:
            raise serializers.ValidationError(
                {"region": "Un usuario regional debe tener una region asignada."}
            )
        return attrs

    def validate_password(self, valor):
        try:
            validate_password(valor)
        except DjangoValidationError as error:
            raise serializers.ValidationError(list(error.messages))
        return valor

    def create(self, datos_validados):
        password = datos_validados.pop("password", None)
        usuario = Usuario(**datos_validados)
        if password:
            usuario.set_password(password)
        else:
            usuario.set_unusable_password()
        usuario.save()
        return usuario

    def update(self, instancia, datos_validados):
        password = datos_validados.pop("password", None)
        for campo, valor in datos_validados.items():
            setattr(instancia, campo, valor)
        if password:
            instancia.set_password(password)
        instancia.save()
        return instancia


class CambiarPasswordSerializer(serializers.Serializer):
    password_actual = serializers.CharField(write_only=True)
    password_nueva = serializers.CharField(write_only=True, min_length=8)

    def validate_password_actual(self, valor):
        if not self.context["request"].user.check_password(valor):
            raise serializers.ValidationError("La contrasena actual no es correcta.")
        return valor

    def validate_password_nueva(self, valor):
        try:
            validate_password(valor, self.context["request"].user)
        except DjangoValidationError as error:
            raise serializers.ValidationError(list(error.messages))
        return valor


class RegistroAccesoSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.nombre_completo", read_only=True)
    username = serializers.CharField(source="usuario.username", read_only=True)
    rol = serializers.CharField(source="usuario.rol", read_only=True)

    class Meta:
        model = RegistroAcceso
        fields = ("id", "username", "usuario_nombre", "rol", "creado_en", "ip")
