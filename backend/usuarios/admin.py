from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import RegistroAcceso, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "nombre_completo", "rol", "region", "ultimo_acceso", "is_active")
    list_filter = ("rol", "region", "is_active")
    search_fields = ("username", "nombre_completo", "email")
    fieldsets = UserAdmin.fieldsets + (
        ("Focos Rojos", {"fields": ("nombre_completo", "rol", "region", "ultimo_acceso")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Focos Rojos", {"fields": ("nombre_completo", "rol", "region")}),
    )
    readonly_fields = ("ultimo_acceso",)


@admin.register(RegistroAcceso)
class RegistroAccesoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "creado_en", "ip")
    list_filter = ("usuario__rol",)
    date_hierarchy = "creado_en"
