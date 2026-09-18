from django.db import models
from django.db.models import Q


class Estatus(models.TextChoices):
    ABIERTA = "ABIERTA", "Abierta"
    EN_PROCESO = "EN_PROCESO", "En proceso"
    CERRADA = "CERRADA", "Cerrada"


class AccionBitacora(models.TextChoices):
    CREACION = "CREACION", "Creacion"
    EDICION = "EDICION", "Edicion"
    CAMBIO_ESTATUS = "CAMBIO_ESTATUS", "Cambio de estatus"
    CIERRE = "CIERRE", "Cierre"
    REAPERTURA = "REAPERTURA", "Reapertura"


class SituacionQuerySet(models.QuerySet):
    def activas(self):
        return self.filter(archivada_en__isnull=True)

    def archivadas(self):
        return self.filter(archivada_en__isnull=False)


class Situacion(models.Model):
    """Un foco rojo de una entidad.

    El `orden` es un entero denso 1..N valido UNICAMENTE entre las situaciones
    activas de la misma entidad. Al archivarse, la situacion suelta su orden.
    Nunca modifiques `orden` directamente: usa `situaciones.services`.
    """

    entidad = models.ForeignKey(
        "catalogos.Entidad",
        verbose_name="entidad",
        on_delete=models.PROTECT,
        related_name="situaciones",
        db_index=True,
    )
    categoria = models.ForeignKey(
        "catalogos.Categoria",
        verbose_name="categoria",
        on_delete=models.PROTECT,
        related_name="situaciones",
    )
    # Texto largo, no un titulo: en el formato real una situacion enumera varios
    # puntos con cifras (ver legacy/Formato_Focos_Rojos_Gira_ejemplo.docx).
    tema = models.TextField("tema")
    # Opcional: en la practica casi siempre se deja en blanco.
    fecha_inicio = models.DateField("fecha de inicio", null=True, blank=True)

    estatus = models.CharField(
        "estatus", max_length=12, choices=Estatus.choices,
        default=Estatus.ABIERTA, db_index=True,
    )
    estatus_detalle = models.TextField("estatus actual")
    acciones = models.TextField("acciones que se estan realizando para solventarlo")

    responsable = models.CharField("responsable", max_length=200)
    fecha_estimada_solucion = models.DateField(
        "fecha estimada de solucion", null=True, blank=True
    )

    orden = models.PositiveIntegerField(
        "orden de importancia", null=True, blank=True,
        help_text="1 = mas urgente. Solo aplica a situaciones activas.",
    )
    archivada_en = models.DateTimeField(
        "archivada en", null=True, blank=True, db_index=True
    )

    creada_por = models.ForeignKey(
        "usuarios.Usuario", verbose_name="creada por", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="situaciones_creadas",
    )
    actualizada_por = models.ForeignKey(
        "usuarios.Usuario", verbose_name="actualizada por", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="situaciones_actualizadas",
    )
    creada_en = models.DateTimeField("creada en", auto_now_add=True)
    actualizada_en = models.DateTimeField("actualizada en", auto_now=True)

    objects = SituacionQuerySet.as_manager()

    class Meta:
        verbose_name = "situacion"
        verbose_name_plural = "situaciones"
        ordering = ["orden", "-creada_en"]
        constraints = [
            # El orden es unico solo entre las activas de una misma entidad.
            models.UniqueConstraint(
                fields=["entidad", "orden"],
                condition=Q(archivada_en__isnull=True),
                name="uniq_orden_entre_activas_por_entidad",
            ),
            # Activa <=> tiene orden. Archivada <=> no lo tiene.
            models.CheckConstraint(
                condition=(
                    Q(archivada_en__isnull=True, orden__isnull=False)
                    | Q(archivada_en__isnull=False, orden__isnull=True)
                ),
                name="orden_solo_en_activas",
            ),
            models.CheckConstraint(
                condition=Q(orden__gte=1) | Q(orden__isnull=True),
                name="orden_positivo",
            ),
        ]
        indexes = [models.Index(fields=["entidad", "archivada_en", "orden"])]

    def __str__(self):
        return f"{self.entidad.nombre}: {self.tema[:60]}"

    @property
    def esta_archivada(self) -> bool:
        return self.archivada_en is not None


class BitacoraSituacion(models.Model):
    """Historial campo a campo. Lo ve cualquiera que pueda ver la situacion.

    Los valores se guardan ya convertidos a texto legible, para que el historial
    sobreviva a un renombrado o fusion de categorias.
    """

    situacion = models.ForeignKey(
        Situacion, verbose_name="situacion", on_delete=models.CASCADE,
        related_name="bitacora",
    )
    usuario = models.ForeignKey(
        "usuarios.Usuario", verbose_name="usuario", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="movimientos_bitacora",
    )
    creado_en = models.DateTimeField("fecha", auto_now_add=True)
    accion = models.CharField("accion", max_length=20, choices=AccionBitacora.choices)
    campo = models.CharField("campo", max_length=40, blank=True)
    valor_anterior = models.TextField("valor anterior", null=True, blank=True)
    valor_nuevo = models.TextField("valor nuevo", null=True, blank=True)

    class Meta:
        verbose_name = "movimiento de bitacora"
        verbose_name_plural = "bitacora"
        ordering = ["-creado_en", "-id"]
        indexes = [models.Index(fields=["situacion", "-creado_en"])]

    def __str__(self):
        return f"{self.get_accion_display()} - {self.campo or 'situacion'}"
