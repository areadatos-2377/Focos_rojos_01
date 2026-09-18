from django.contrib import admin

from .models import Categoria, Entidad, Region


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "clave", "orden")


@admin.register(Entidad)
class EntidadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "clave", "region", "activa")
    list_filter = ("region", "activa")
    search_fields = ("nombre",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "nombre_normalizado", "creada_por", "creada_en", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre",)
