from django.urls import path
from . import views

app_name = 'pedidos'

urlpatterns = [
    path('', views.pedido_list, name='list'),
    path('nuevo/', views.pedido_create, name='create'),
    path('<int:pk>/', views.pedido_detail, name='detail'),
    path('<int:pk>/estado/', views.pedido_cambiar_estado, name='cambiar_estado'),
    path('<int:pk>/entregar/', views.pedido_marcar_entregado, name='marcar_entregado'),
]
