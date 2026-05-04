from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    path('', views.producto_list, name='list'),
    path('<str:pk>/', views.producto_detail, name='detail'),
]
