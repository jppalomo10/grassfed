from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum

from core.models import (
    Cliente, Producto, Pedido,
    VwStockActual, VwPendienteDeEntrega,
)


@login_required
def index(request):
    ventas_totales = (
        Pedido.objects.filter(Estado='Pagado').aggregate(t=Sum('Total'))['t'] or 0
    )
    stock_bajo = list(
        VwStockActual.objects.filter(Estado_Stock__in=['BAJO', 'AGOTADO'])
        .order_by('Estado_Stock', 'SKU')
    )
    ultimos_pedidos = list(
        Pedido.objects.select_related('Cliente')
        .order_by('-Creado_En')[:10]
    )

    context = {
        'total_clientes': Cliente.objects.count(),
        'total_productos': Producto.objects.filter(Activo=True).count(),
        'pedidos_pendientes_pago': Pedido.objects.filter(Estado='Pendiente de Pago').count(),
        'pedidos_pagados': Pedido.objects.filter(Estado='Pagado').count(),
        'pedidos_anulados': Pedido.objects.filter(Estado='Anulado').count(),
        'pedidos_pendientes_entrega': VwPendienteDeEntrega.objects.count(),
        'ventas_totales': ventas_totales,
        'stock_bajo': stock_bajo,
        'ultimos_pedidos': ultimos_pedidos,
    }
    return render(request, 'dashboard/index.html', context)
