from django.contrib import admin

from .models import Canal, Categoria, Creador, Plataforma


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)


@admin.register(Plataforma)
class PlataformaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'url')


@admin.register(Canal)
class CanalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'seguidores')
    list_filter = ('categoria', 'plataformas')
    filter_horizontal = ('plataformas',)


@admin.register(Creador)
class CreadorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'canal')
