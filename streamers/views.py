from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, F, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView,
)

from .forms import CanalForm, CreadorForm
from .models import Canal, Categoria, Creador, Plataforma

# Clave de la sesión con los canales que ya ha seguido el visitante.
SESION_SEGUIDOS = 'canales_seguidos'


# ---------------------------------------------------------------------------
# Páginas públicas (vistas genéricas basadas en clases)
# ---------------------------------------------------------------------------

class PortadaView(TemplateView):
    template_name = 'portada.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Un canal por categoría: el que más seguidores tiene.
        # Rendimiento: una sola consulta en lugar de una por categoría.
        destacados = {}
        canales = Canal.objects.select_related('categoria').order_by('categoria__nombre', '-seguidores')
        for canal in canales:
            destacados.setdefault(canal.categoria_id, canal)
        context['destacados'] = list(destacados.values())
        return context


class CanalListView(ListView):
    model = Canal
    template_name = 'canal_list.html'

    def get_queryset(self):
        queryset = Canal.objects.select_related('categoria')
        # Búsqueda sin JavaScript (?q=...). Con JavaScript se hace por AJAX.
        self.q = self.request.GET.get('q', '').strip()
        if self.q:
            queryset = queryset.filter(nombre__icontains=self.q)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.q
        return context


class CanalDetailView(DetailView):
    model = Canal
    template_name = 'canal_detail.html'
    queryset = (Canal.objects
                .select_related('categoria', 'creador')
                .prefetch_related('plataformas'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['siguiendo'] = self.object.pk in self.request.session.get(SESION_SEGUIDOS, [])
        return context


class CategoriaListView(ListView):
    model = Categoria
    template_name = 'categoria_list.html'
    # Rendimiento: el número de canales se calcula en la misma consulta.
    queryset = Categoria.objects.annotate(num_canales=Count('canales'))


class CategoriaDetailView(DetailView):
    model = Categoria
    template_name = 'categoria_detail.html'
    queryset = Categoria.objects.prefetch_related('canales')


class PlataformaListView(ListView):
    model = Plataforma
    template_name = 'plataforma_list.html'
    queryset = Plataforma.objects.annotate(num_canales=Count('canales'))


class PlataformaDetailView(DetailView):
    model = Plataforma
    template_name = 'plataforma_detail.html'
    queryset = Plataforma.objects.prefetch_related(
        Prefetch('canales', queryset=Canal.objects.select_related('categoria'))
    )


# ---------------------------------------------------------------------------
# Formularios públicos (ModelForm + vistas genéricas de edición)
# Seguridad: hay que iniciar sesión y tener el permiso de Django
# correspondiente (los mismos que dan los roles de "crear_roles").
# Sin sesión -> página de inicio de sesión; sin permiso -> error 403.
# ---------------------------------------------------------------------------

class CanalFormMixin:
    """Pasa el usuario al formulario (decide si puede tocar los seguidores)."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class CanalCreateView(PermissionRequiredMixin, CanalFormMixin, SuccessMessageMixin, CreateView):
    permission_required = 'streamers.add_canal'
    model = Canal
    form_class = CanalForm
    template_name = 'canal_form.html'
    success_message = _('El canal «%(nombre)s» se ha creado correctamente.')


class CanalUpdateView(PermissionRequiredMixin, CanalFormMixin, SuccessMessageMixin, UpdateView):
    permission_required = 'streamers.change_canal'
    model = Canal
    form_class = CanalForm
    template_name = 'canal_form.html'
    success_message = _('Los cambios en «%(nombre)s» se han guardado.')


class CanalDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    permission_required = 'streamers.delete_canal'
    model = Canal
    template_name = 'canal_confirm_delete.html'
    success_url = reverse_lazy('canal_list')
    success_message = _('El canal se ha eliminado.')


class CreadorCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    """Añade el creador de un canal que todavía no tiene."""
    permission_required = 'streamers.add_creador'
    model = Creador
    form_class = CreadorForm
    template_name = 'creador_form.html'
    success_message = _('Se ha añadido a %(nombre)s como creador del canal.')

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            return self.handle_no_permission()
        self.canal = get_object_or_404(Canal, pk=kwargs['canal_pk'])
        if hasattr(self.canal, 'creador'):
            # Ya tiene creador (relación 1:1): se edita en lugar de crear otro.
            return redirect('creador_update', pk=self.canal.creador.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.canal = self.canal
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['canal'] = self.canal
        return context

    def get_success_url(self):
        return reverse('canal_detail', args=[self.canal.pk])


class CreadorUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    permission_required = 'streamers.change_creador'
    model = Creador
    form_class = CreadorForm
    template_name = 'creador_form.html'
    success_message = _('Los datos de %(nombre)s se han guardado.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['canal'] = self.object.canal
        return context

    def get_success_url(self):
        return reverse('canal_detail', args=[self.object.canal_id])


# ---------------------------------------------------------------------------
# AJAX (respuestas JSON para el JavaScript de static/js/streamers.js)
# ---------------------------------------------------------------------------

class CanalBusquedaJsonView(View):
    """GET /api/canales/?q=texto -> lista de canales en JSON (búsqueda en vivo)."""
    max_resultados = 20

    def get(self, request):
        q = request.GET.get('q', '').strip()
        canales = Canal.objects.select_related('categoria')
        if q:
            canales = canales.filter(nombre__icontains=q)
        datos = [
            {
                'nombre': canal.nombre,
                'url': canal.get_absolute_url(),
                'categoria': canal.categoria.nombre,
                'categoria_url': reverse('categoria_detail', args=[canal.categoria_id]),
                'seguidores': canal.seguidores,
            }
            for canal in canales[:self.max_resultados]
        ]
        return JsonResponse({'q': q, 'total': len(datos), 'canales': datos})


class SeguirCanalView(View):
    """POST /canales/<pk>/seguir/ -> suma un seguidor.

    Cada visitante solo suma una vez por canal: los canales que ya ha seguido
    se guardan en su sesión (seguridad: evita inflar los seguidores a base de clics).
    Con AJAX responde JSON; sin JavaScript (formulario normal) redirige al detalle.
    """

    def post(self, request, pk):
        canal = get_object_or_404(Canal, pk=pk)
        seguidos = request.session.get(SESION_SEGUIDOS, [])
        if canal.pk not in seguidos:
            # F() hace la suma en la base de datos: evita perder clics simultáneos.
            Canal.objects.filter(pk=canal.pk).update(seguidores=F('seguidores') + 1)
            canal.refresh_from_db(fields=['seguidores'])
            request.session[SESION_SEGUIDOS] = seguidos + [canal.pk]

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'seguidores': canal.seguidores, 'siguiendo': True})
        return redirect(canal)
