from django.db import models

from .normalizacion import normalizar_nombre


class Region(models.Model):
    """Region operativa. Catalogo fijo: 5 regiones."""

    clave = models.SlugField("clave", max_length=20, unique=True)
    nombre = models.CharField("nombre", max_length=60, unique=True)
    orden = models.PositiveSmallIntegerField("orden", default=0)

    class Meta:
        verbose_name = "region"
        verbose_name_plural = "regiones"
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Entidad(models.Model):
    """Entidad federativa. Catalogo fijo: 24 entidades, cada una en UNA region."""

    clave = models.SlugField("clave", max_length=30, unique=True)
    nombre = models.CharField("nombre", max_length=80, unique=True)
    region = models.ForeignKey(
        Region,
        verbose_name="region",
        on_delete=models.PROTECT,
        related_name="entidades",
        db_index=True,
    )
    activa = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "entidad"
        verbose_name_plural = "entidades"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    """Categoria de situacion. Catalogo global que cualquier usuario puede ampliar.

    `nombre_normalizado` es unico en base de datos: es lo que impide registrar la
    misma categoria escrita de dos formas distintas.
    """

    nombre = models.CharField("nombre", max_length=120)
    nombre_normalizado = models.CharField(
        "nombre normalizado", max_length=120, unique=True, editable=False
    )
    creada_por = models.ForeignKey(
        "usuarios.Usuario",
        verbose_name="creada por",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="categorias_creadas",
    )
    creada_en = models.DateTimeField("creada en", auto_now_add=True)
    activa = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "categoria"
        verbose_name_plural = "categorias"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        self.nombre = " ".join(self.nombre.split())
        self.nombre_normalizado = normalizar_nombre(self.nombre)
        super().save(*args, **kwargs)
