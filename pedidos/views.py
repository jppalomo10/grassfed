import json
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import connections
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from core.db_router import _thread_locals
from core.decorators import role_required
from core.models import Pedido, Cliente, Producto, DetallePedido
from core.utils import friendly_db_error


def _get_alias():
    return getattr(_thread_locals, 'db_alias', 'dev')


@login_required
def pedido_list(request):
    qs = Pedido.objects.select_related('Cliente').order_by('-Fecha', '-ID_Pedido')

    estado = request.GET.get('estado', '')
    cliente_q = request.GET.get('cliente', '')
    entregado = request.GET.get('entregado', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    if estado:
        qs = qs.filter(Estado=estado)
    if cliente_q:
        qs = qs.filter(Cliente__Nombre__icontains=cliente_q) | \
             Pedido.objects.filter(Cliente__Telefono__icontains=cliente_q)
        qs = qs.select_related('Cliente').order_by('-Fecha', '-ID_Pedido')
    if entregado == '1':
        qs = qs.filter(Entregado=True)
    elif entregado == '0':
        qs = qs.filter(Entregado=False)
    if fecha_desde:
        qs = qs.filter(Fecha__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(Fecha__lte=fecha_hasta)

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'pedidos/list.html', {
        'page': page,
        'estado': estado,
        'cliente_q': cliente_q,
        'entregado': entregado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'estados': ['Pendiente de Pago', 'Pagado', 'Anulado'],
    })


@login_required
def pedido_detail(request, pk):
    pedido = get_object_or_404(Pedido.objects.select_related('Cliente'), pk=pk)
    detalles = (
        DetallePedido.objects
        .filter(ID_Pedido=pk)
        .select_related('SKU')
    )
    return render(request, 'pedidos/detail.html', {
        'pedido': pedido,
        'detalles': detalles,
    })


@login_required
def pedido_create(request):
    clientes = Cliente.objects.order_by('Nombre')
    productos = Producto.objects.filter(Activo=True).order_by('Producto')
    cliente_presel = request.GET.get('cliente', '')

    if request.method == 'POST':
        p_fecha = request.POST.get('fecha', str(date.today()))
        p_cliente = request.POST.get('cliente', '').strip()
        p_pago = request.POST.get('pago', '')
        p_envio = request.POST.get('envio', '').strip() or None

        skus = request.POST.getlist('sku[]')
        pesos = request.POST.getlist('peso[]')
        precios = request.POST.getlist('precio[]')
        descuentos = request.POST.getlist('descuento[]')
        cantidades = request.POST.getlist('cantidad[]')

        if not skus or not p_cliente or not p_pago:
            messages.error(request, 'Complete todos los campos obligatorios y agregue al menos un producto.')
            return render(request, 'pedidos/form.html', {
                'clientes': clientes, 'productos': productos,
                'cliente_presel': p_cliente,
            })

        detalles = []
        for i, sku in enumerate(skus):
            if not sku:
                continue
            try:
                linea = {
                    'sku': sku,
                    'peso': float(pesos[i]) if pesos[i] else 0,
                    'precio': float(precios[i]) if precios[i] else 0,
                    'descuento': float(descuentos[i]) if descuentos[i] else 0,
                }
                if cantidades[i]:
                    linea['cantidad'] = int(cantidades[i])
                detalles.append(linea)
            except (ValueError, IndexError):
                messages.error(request, 'Valores inválidos en las líneas del pedido.')
                return render(request, 'pedidos/form.html', {
                    'clientes': clientes, 'productos': productos,
                    'cliente_presel': p_cliente,
                })

        json_detalles = json.dumps(detalles)
        alias = _get_alias()
        try:
            with connections[alias].cursor() as cursor:
                cursor.execute(
                    "CALL sp_RegistrarPedido(%s, %s, %s, %s, %s, @pid)",
                    [p_fecha, p_cliente, p_pago, p_envio, json_detalles]
                )
                cursor.execute("SELECT @pid")
                pedido_id = cursor.fetchone()[0]
            messages.success(request, f'Pedido #{pedido_id} registrado correctamente.')
            return redirect('pedidos:detail', pk=pedido_id)
        except Exception as e:
            messages.error(request, friendly_db_error(e))

    return render(request, 'pedidos/form.html', {
        'clientes': clientes,
        'productos': productos,
        'cliente_presel': cliente_presel,
        'today': str(date.today()),
        'pago_choices': ['Efectivo', 'Transferencia', 'Tarjeta'],
    })


@require_POST
@role_required('admin', 'dev')
def pedido_cambiar_estado(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    nuevo_estado = request.POST.get('estado', '')
    if nuevo_estado not in ('Pendiente de Pago', 'Pagado', 'Anulado'):
        messages.error(request, 'Estado inválido.')
        return redirect('pedidos:detail', pk=pk)

    if nuevo_estado == 'Anulado':
        motivo = request.POST.get('motivo', 'Sin motivo').strip() or 'Sin motivo'
        alias = _get_alias()
        try:
            with connections[alias].cursor() as cursor:
                cursor.execute("CALL sp_AnularPedido(%s, %s)", [pk, motivo])
            messages.success(request, f'Pedido #{pk} anulado correctamente.')
        except Exception as e:
            messages.error(request, friendly_db_error(e))
    else:
        try:
            pedido.Estado = nuevo_estado
            pedido.save(update_fields=['Estado'])
            messages.success(request, f'Estado actualizado a "{nuevo_estado}".')
        except Exception as e:
            messages.error(request, friendly_db_error(e))

    return redirect('pedidos:detail', pk=pk)


@require_POST
@role_required('admin', 'dev')
def pedido_marcar_entregado(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    try:
        pedido.Entregado = True
        pedido.save(update_fields=['Entregado'])
        messages.success(request, f'Pedido #{pk} marcado como entregado.')
    except Exception as e:
        messages.error(request, friendly_db_error(e))
    return redirect('pedidos:detail', pk=pk)
