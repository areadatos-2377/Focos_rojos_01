from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class Rol(models.TextChoices):
    REGIONAL = "REGIONAL", "Regional"
    ADMINISTRADOR = "ADMINISTRADOR", "Administrador"
    SUPER_ADMIN = "SUPER_ADMIN", "Super administrador"


class Usuario(AbstractUser):
    """Usuario del sistema.

    `is_staff` / `is_superuser` solo gobiernan el admin de Django; el control de
    acceso de la aplicacion se basa exclusivamente en `rol`.
    """

    nombre_completo = models.CharField("nombre completo", max_length=150, blank=True)
    rol = models.CharField(
        "rol", max_length=15, choices=Rol.choices, default=Rol.REGIONAL, db_index=True
    )
    region = models.ForeignKey(
        "catalogos.Region",
        verbose_name="region",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios",
        help_text="Obligatoria para el rol Regional; vacia para los demas roles.",
    )
    ultimo_acceso = models.DateTimeField(
        "ultimo acceso", null=True, blank=True, db_index=True
    )

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        constraints = [
            models.CheckConstraint(
                condition=~Q(rol=Rol.REGIONAL) | Q(region__isnull=False),
                name="usuario_regional_requiere_region",
            ),
        ]

    def __str__(self):
        return self.nombre_completo or self.username

    @property
    def es_admin(self) -> bool:
        return self.rol in (Rol.ADMINISTRADOR, Rol.SUPER_ADMIN)

    def save(self, *args, **kwargs):
        if self.rol == Rol.SUPER_ADMIN:
            self.is_staff = True
        if self.rol != Rol.REGIONAL:
            self.region = None
        super().save(*args, **kwargs)


class RegistroAcceso(models.Model):
    """Una fila por inicio de sesion exitoso. Solo lo consultan los administradores."""

    usuario = models.ForeignKey(
        Usuario, on_delete=models.CASCADE, related_name="accesos", verbose_name="usuario"
    )
    creado_en = models.DateTimeField("fecha", auto_now_add=True)
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.CharField("navegador", max_length=300, blank=True)

    class Meta:
        verbose_name = "registro de acceso"
        verbose_name_plural = "registros de acceso"
        indexes = [models.Index(fields=["usuario", "-creado_en"])]
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.usuario} - {self.creado_en:%d/%m/%Y %H:%M}"
