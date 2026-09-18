from django.contrib import admin

from .models import BitacoraSituacion, Situacion


class BitacoraInline(admin.TabularInline):
    model = BitacoraSituacion
    extra = 0
    can_delete = False
    readonly_fields = ("creado_en", "usuario", "accion", "campo",
                       "valor_anterior", "valor_nuevo")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Situacion)
class SituacionAdmin(admin.ModelAdmin):
    list_display = ("tema", "entidad", "categoria", "estatus", "orden", "archivada_en")
    list_filter = ("entidad__region", "entidad", "estatus", "categoria")
    search_fields = ("tema", "responsable")
    readonly_fields = ("orden", "archivada_en", "creada_por", "actualizada_por")
    inlines = [BitacoraInline]
