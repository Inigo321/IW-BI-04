from django.views.generic import DetailView, ListView, TemplateView

from .models import Canal, Categoria, Plataforma


class PortadaView(TemplateView):
    template_name = 'portada.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Un canal por categoría: el que más seguidores tiene
        destacados = []
        for categoria in Categoria.objects.all():
            canal = categoria.canales.order_by('-seguidores').first()
            if canal:
                destacados.append(canal)
        context['destacados'] = destacados
        return context


class CanalListView(ListView):
    model = Canal
    template_name = 'canal_list.html'
    queryset = Canal.objects.select_related('categoria')


class CanalDetailView(DetailView):
    model = Canal
    template_name = 'canal_detail.html'


class CategoriaListView(ListView):
    model = Categoria
    template_name = 'categoria_list.html'


class CategoriaDetailView(DetailView):
    model = Categoria
    template_name = 'categoria_detail.html'


class PlataformaListView(ListView):
    model = Plataforma
    template_name = 'plataforma_list.html'


class PlataformaDetailView(DetailView):
    model = Plataforma
    template_name = 'plataforma_detail.html'
