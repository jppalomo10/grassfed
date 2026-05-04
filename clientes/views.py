from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404

from core.models import Cliente, Pedido
from core.utils import call_function, friendly_db_error
from core.decorators import role_required
from .forms import ClienteForm


@login_required
def cliente_list(request):
    q = request.GET.get('q', '').strip()
    qs = Cliente.objects.order_by('Nombre')
    if q:
        qs = qs.filter(
            Nombre__icontains=q
        ) | qs.filter(
            Telefono__icontains=q
        ) | qs.filter(
            NIT__icontains=q
        ) | qs.filter(
            Correo__icontains=q
        )
        qs = qs.order_by('Nombre')

    paginator = Paginator(qs, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'clientes/list.html', {'page': page, 'q': q})


@login_required
def cliente_detail(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    deuda = call_function('fn_DeudaCliente', [pk])
    pedidos = Pedido.objects.filter(Cliente=pk).order_by('-Fecha')[:20]
    return render(request, 'clientes/detail.html', {
        'cliente': cliente,
        'deuda': deuda or 0,
        'pedidos': pedidos,
    })


@login_required
def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            try:
                # Use today's date for Fecha_Alta since it has no default via ORM
                from datetime import date
                obj = form.save(commit=False)
                obj.Fecha_Alta = date.today()
                obj.save()
                messages.success(request, f'Cliente "{obj.Nombre}" creado correctamente.')
                return redirect('clientes:detail', pk=obj.pk)
            except Exception as e:
                messages.error(request, friendly_db_error(e))
    else:
        form = ClienteForm()
    return render(request, 'clientes/form.html', {'form': form, 'action': 'Crear'})


@role_required('admin', 'dev')
def cliente_edit(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Cliente actualizado correctamente.')
                return redirect('clientes:detail', pk=pk)
            except Exception as e:
                messages.error(request, friendly_db_error(e))
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'clientes/form.html', {
        'form': form, 'action': 'Editar', 'cliente': cliente,
    })
