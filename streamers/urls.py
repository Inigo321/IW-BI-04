from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.PortadaView.as_view(), name='portada'),

    # Canales
    path('canales/', views.CanalListView.as_view(), name='canal_list'),
    path('canales/nuevo/', views.CanalCreateView.as_view(), name='canal_create'),
    path('canales/<int:pk>/', views.CanalDetailView.as_view(), name='canal_detail'),
    path('canales/<int:pk>/editar/', views.CanalUpdateView.as_view(), name='canal_update'),
    path('canales/<int:pk>/borrar/', views.CanalDeleteView.as_view(), name='canal_delete'),
    path('canales/<int:pk>/seguir/', views.SeguirCanalView.as_view(), name='canal_seguir'),

    # Creadores (relación 1:1 con el canal)
    path('canales/<int:canal_pk>/creador/nuevo/', views.CreadorCreateView.as_view(), name='creador_create'),
    path('creadores/<int:pk>/editar/', views.CreadorUpdateView.as_view(), name='creador_update'),

    # Categorías y plataformas
    path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),
    path('categorias/<int:pk>/', views.CategoriaDetailView.as_view(), name='categoria_detail'),
    path('plataformas/', views.PlataformaListView.as_view(), name='plataforma_list'),
    path('plataformas/<int:pk>/', views.PlataformaDetailView.as_view(), name='plataforma_detail'),

    # Inicio y cierre de sesión (para usar los formularios públicos)
    path('cuentas/entrar/', auth_views.LoginView.as_view(), name='login'),
    path('cuentas/salir/', auth_views.LogoutView.as_view(), name='logout'),

    # AJAX
    path('api/canales/', views.CanalBusquedaJsonView.as_view(), name='api_canales'),
]
