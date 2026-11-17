from django.contrib import admin, messages
from django.db.models import Count
from django.utils.translation import gettext_lazy as _, ngettext

from .models import Canal, Categoria, Creador, Plataforma

# ---------------------------------------------------------------------------
# Textos generales del panel (el diseño está en templates/admin/base_site.html)
# ---------------------------------------------------------------------------
admin.site.site_header = _('Streamers United · Administración')
admin.site.site_title = 'Streamers United'
admin.site.index_title = _('Gestión de contenidos')

# Nombre del grupo cuyos miembros pueden modificar los seguidores a mano.
GRUPO_ADMINISTRADORES = 'Administradores de contenido'


def es_administrador_de_contenido(user):
    return user.is_superuser or user.groups.filter(name=GRUPO_ADMINISTRADORES).exists()


class CanalInline(admin.TabularInline):
    """Canales de una categoría, de solo lectura, dentro de la ficha de la categoría."""
    model = Canal
    fields = ('nombre', 'seguidores')
    readonly_fields = ('nombre', 'seguidores')
    extra = 0
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'num_canales')
    search_fields = ('nombre', 'descripcion')
    inlines = [CanalInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_num_canales=Count('canales'))

    @admin.display(description=_('Nº de canales'), ordering='_num_canales')
    def num_canales(self, obj):
        return obj._num_canales


@admin.register(Plataforma)
class PlataformaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'url', 'num_canales')
    search_fields = ('nombre',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_num_canales=Count('canales'))

    @admin.display(description=_('Nº de canales'), ordering='_num_canales')
    def num_canales(self, obj):
        return obj._num_canales


class CreadorInline(admin.StackedInline):
    """El creador (relación 1:1) se edita dentro de la ficha del canal."""
    model = Creador
    can_delete = False
    extra = 0


@admin.register(Canal)
class CanalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'seguidores', 'lista_plataformas', 'tiene_creador')
    list_filter = ('categoria', 'plataformas')
    list_select_related = ('categoria', 'creador')
    search_fields = ('nombre', 'descripcion', 'creador__nombre')
    filter_horizontal = ('plataformas',)
    list_per_page = 20
    inlines = [CreadorInline]
    actions = ['poner_seguidores_a_cero']
    fieldsets = (
        (None, {'fields': ('nombre', 'categoria', 'descripcion')}),
        (_('Audiencia'), {'fields': ('seguidores', 'plataformas')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('plataformas')

    @admin.display(description=_('Plataformas'))
    def lista_plataformas(self, obj):
        return ', '.join(p.nombre for p in obj.plataformas.all()) or '-'

    @admin.display(description=_('Creador'), boolean=True)
    def tiene_creador(self, obj):
        return hasattr(obj, 'creador')

    # --- Comportamiento según el rol ------------------------------------
    def get_readonly_fields(self, request, obj=None):
        """Solo los administradores de contenido pueden tocar los seguidores a mano."""
        if es_administrador_de_contenido(request.user):
            return ()
        return ('seguidores',)

    def get_list_editable(self, request):
        return ('seguidores',) if es_administrador_de_contenido(request.user) else ()

    def get_changelist_instance(self, request):
        # list_editable depende del usuario: se ajusta antes de construir el listado.
        self.list_editable = self.get_list_editable(request)
        return super().get_changelist_instance(request)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not es_administrador_de_contenido(request.user):
            actions.pop('poner_seguidores_a_cero', None)
        return actions

    @admin.action(description=_('Poner a cero los seguidores de los canales seleccionados'),
                  permissions=['change'])
    def poner_seguidores_a_cero(self, request, queryset):
        total = queryset.update(seguidores=0)
        texto = ngettext('Se ha reiniciado %(total)d canal.', 'Se han reiniciado %(total)d canales.', total)
        self.message_user(request, texto % {'total': total}, messages.SUCCESS)


@admin.register(Creador)
class CreadorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'canal')
    list_select_related = ('canal',)
    search_fields = ('nombre', 'canal__nombre')
    autocomplete_fields = ('canal',)
