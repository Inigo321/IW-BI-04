from django.urls import path

from . import views

urlpatterns = [
    path('', views.PortadaView.as_view(), name='portada'),
    path('canales/', views.CanalListView.as_view(), name='canal_list'),
    path('canales/<int:pk>/', views.CanalDetailView.as_view(), name='canal_detail'),
    path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),
    path('categorias/<int:pk>/', views.CategoriaDetailView.as_view(), name='categoria_detail'),
    path('plataformas/', views.PlataformaListView.as_view(), name='plataforma_list'),
    path('plataformas/<int:pk>/', views.PlataformaDetailView.as_view(), name='plataforma_detail'),
]
