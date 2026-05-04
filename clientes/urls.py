from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.cliente_list, name='list'),
    path('nuevo/', views.cliente_create, name='create'),
    path('<str:pk>/', views.cliente_detail, name='detail'),
    path('<str:pk>/editar/', views.cliente_edit, name='edit'),
]
