from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', include('dashboard.urls')),
    path('clientes/', include('clientes.urls')),
    path('productos/', include('productos.urls')),
    path('pedidos/', include('pedidos.urls')),
    path('reportes/', include('reportes.urls')),
    path('dev/', include('dev.urls')),
]
