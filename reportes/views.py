from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from core.decorators import role_required
from core.models import (
    VwStockActual, VwPendienteDePago, VwPendienteDeEntrega,
    VwVentaPorProducto, VwVentaPorCliente, VwVentaPorFecha,
    VwFacturaCompleta,
)
from core.utils import call_procedure, export_csv


@login_required
def index(request):
    return render(request, 'reportes/index.html')


# ── Stock ──────────────────────────────────────────────────────────

@role_required('admin', 'dev')
def reporte_stock(request):
    qs = VwStockActual.objects.order_by('Estado_Stock', 'Producto')
    if request.GET.get('export') == 'csv':
        return export_csv(
            qs, 'stock_actual',
            ['SKU', 'Producto', 'Stock_Minimo', 'Ingresos_lb',
             'Transf_Salida_lb', 'Ventas_lb', 'Stock_lb', 'Estado_Stock'],
        )
    return render(request, 'reportes/stock.html', {'stock': qs})


# ── Pendientes de pago ─────────────────────────────────────────────

@role_required('admin', 'dev')
def reporte_pendientes_pago(request):
    qs = VwPendienteDePago.objects.order_by('-Dias_Vencimiento')
    envio_q = request.GET.get('envio', '').strip()
    if envio_q:
        qs = qs.filter(Envio__icontains=envio_q)
    if request.GET.get('export') == 'csv':
        return export_csv(
            qs, 'pendientes_pago',
            ['ID_Pedido', 'Fecha', 'Dias_Vencimiento', 'Cliente', 'Telefono',
             'Total', 'Pago', 'Envio', 'Entregado'],
        )
    return render(request, 'reportes/pendientes_pago.html', {'rows': qs, 'envio_q': envio_q})


# ── Pendientes de entrega ──────────────────────────────────────────

@role_required('admin', 'dev')
def reporte_pendientes_entrega(request):
    qs = VwPendienteDeEntrega.objects.order_by('Envio', 'Cliente')
    envio_q = request.GET.get('envio', '').strip()
    if envio_q:
        qs = qs.filter(Envio__icontains=envio_q)
    if request.GET.get('export') == 'csv':
        return export_csv(
            qs, 'pendientes_entrega',
            ['ID_Pedido', 'Fecha', 'Cliente', 'Telefono', 'Direccion',
             'Total', 'Envio', 'Peso_Total_lb'],
        )
    return render(request, 'reportes/pendientes_entrega.html', {'rows': qs, 'envio_q': envio_q})


# ── Ventas por producto ────────────────────────────────────────────

@role_required('admin', 'dev')
def reporte_ventas_producto(request):
    qs = VwVentaPorProducto.objects.order_by('-Total_Q')
    if request.GET.get('export') == 'csv':
        return export_csv(
            qs, 'ventas_por_producto',
            ['SKU', 'Producto', 'Num_Pedidos', 'Peso_Total_lb', 'Total_Q', 'Precio_Promedio'],
        )
    return render(request, 'reportes/ventas_producto.html', {'rows': qs})


# ── Ventas por cliente ─────────────────────────────────────────────

@role_required('admin', 'dev')
def reporte_ventas_cliente(request):
    qs = VwVentaPorCliente.objects.order_by('-Total_Comprado_Q')
    if request.GET.get('export') == 'csv':
        return export_csv(
            qs, 'ventas_por_cliente',
            ['Telefono', 'Nombre', 'NIT', 'Num_Pedidos',
             'Total_Comprado_Q', 'Deuda_Q', 'Ultima_Compra'],
        )
    return render(request, 'reportes/ventas_cliente.html', {'rows': qs})


# ── Ventas por fecha ───────────────────────────────────────────────

@role_required('admin', 'dev')
def reporte_ventas_fecha(request):
    qs = VwVentaPorFecha.objects.order_by('-Fecha')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    if fecha_desde:
        qs = qs.filter(Fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(Fecha__lte=fecha_hasta)
    if request.GET.get('export') == 'csv':
        return export_csv(qs, 'ventas_por_fecha', ['Fecha', 'Num_Pedidos', 'Total_Q'])
    return render(request, 'reportes/ventas_fecha.html', {
        'rows': qs, 'fecha_desde': fecha_desde, 'fecha_hasta': fecha_hasta,
    })


# ── Reporte de ventas (sp_ReporteVentas) ──────────────────────────

@role_required('admin', 'dev')
def reporte_ventas_sp(request):
    """Calls sp_ReporteVentas(fecha_inicio, fecha_fin) — 3 result sets."""
    resumen = []
    por_producto = []
    por_pago = []
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    if fecha_desde and fecha_hasta:
        try:
            results = call_procedure('sp_ReporteVentas', [fecha_desde, fecha_hasta])
            if len(results) > 0 and results[0]:
                resumen = results[0]
            if len(results) > 1 and results[1]:
                por_producto = results[1]
            if len(results) > 2 and results[2]:
                por_pago = results[2]
        except Exception:
            pass

    if request.GET.get('export') == 'csv' and por_producto:
        return export_csv(
            por_producto, 'reporte_ventas',
            ['Producto', 'peso_lb', 'total_q'],
        )

    return render(request, 'reportes/ventas_sp.html', {
        'resumen': resumen,
        'por_producto': por_producto,
        'por_pago': por_pago,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    })


# ── Factura / detalle de pedido ────────────────────────────────────

@login_required
def factura(request, pedido_id):
    lineas = VwFacturaCompleta.objects.filter(ID_Pedido=pedido_id).order_by('SKU')
    if not lineas.exists():
        from django.http import Http404
        raise Http404
    header = lineas[0]
    return render(request, 'reportes/factura.html', {
        'header': header,
        'lineas': lineas,
    })
