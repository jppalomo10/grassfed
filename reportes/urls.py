from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.index, name='index'),
    path('stock/', views.reporte_stock, name='stock'),
    path('pendientes-pago/', views.reporte_pendientes_pago, name='pendientes_pago'),
    path('pendientes-entrega/', views.reporte_pendientes_entrega, name='pendientes_entrega'),
    path('ventas-producto/', views.reporte_ventas_producto, name='ventas_producto'),
    path('ventas-cliente/', views.reporte_ventas_cliente, name='ventas_cliente'),
    path('ventas-fecha/', views.reporte_ventas_fecha, name='ventas_fecha'),
    path('ventas-sp/', views.reporte_ventas_sp, name='ventas_sp'),
    path('factura/<int:pedido_id>/', views.factura, name='factura'),
]
