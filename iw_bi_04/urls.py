"""
URL configuration for iw_bi_04 project.

Multilingüismo (E4a - opción 6): todas las páginas llevan el idioma delante,
por ejemplo /es/canales/ y /en/canales/. Si se entra en /, LocaleMiddleware
redirige al idioma del navegador (o al español por defecto).
"""
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Vista de Django que cambia de idioma (la usa el selector de base.html)
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('streamers.urls')),
)
