from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404

from core.models import Producto, VwStockActual, MovimientoInventario
from core.utils import call_function


@login_required
def producto_list(request):
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '')

    stock_qs = VwStockActual.objects.all()
    if q:
        stock_qs = stock_qs.filter(SKU__icontains=q) | VwStockActual.objects.filter(Producto__icontains=q)
        stock_qs = stock_qs.order_by('SKU')
    if estado:
        stock_qs = stock_qs.filter(Estado_Stock=estado)

    stock_qs = stock_qs.order_by('Estado_Stock', 'Producto')
    paginator = Paginator(stock_qs, 25)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'productos/list.html', {'page': page, 'q': q, 'estado': estado})


@login_required
def producto_detail(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    stock_live = call_function('fn_StockProducto', [pk])
    movimientos = MovimientoInventario.objects.filter(SKU=pk).order_by('-Fecha')[:30]
    try:
        stock_view = VwStockActual.objects.get(pk=pk)
    except VwStockActual.DoesNotExist:
        stock_view = None
    return render(request, 'productos/detail.html', {
        'producto': producto,
        'stock_live': stock_live or 0,
        'stock_view': stock_view,
        'movimientos': movimientos,
    })
