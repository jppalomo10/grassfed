from django.contrib import admin
from .models import (
    CatalogoCuenta, Producto, Cliente,
    Pedido, DetallePedido, MovimientoInventario,
    AsientoContable, Bitacora,
)

# All admin queries run through the 'dev' connection (full access)
_USING = 'dev'


class ERPModelAdmin(admin.ModelAdmin):
    """Base admin that routes all queries to the dev MySQL connection."""
    using = _USING

    def save_model(self, _request, obj, _form, _change):
        obj.save(using=self.using)

    def delete_model(self, _request, obj):
        obj.delete(using=self.using)

    def get_queryset(self, request):
        return super().get_queryset(request).using(self.using)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        kwargs['queryset'] = db_field.related_model.objects.using(self.using)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Cliente)
class ClienteAdmin(ERPModelAdmin):
    list_display = ['Telefono', 'Nombre', 'NIT', 'Correo', 'Fecha_Alta']
    search_fields = ['Nombre', 'Telefono', 'NIT', 'Correo']
    list_filter = ['Fecha_Alta']
    ordering = ['Nombre']


@admin.register(Producto)
class ProductoAdmin(ERPModelAdmin):
    list_display = ['SKU', 'Producto', 'Precio', 'Stock_Minimo', 'Activo', 'Fecha_Alta']
    search_fields = ['SKU', 'Producto']
    list_filter = ['Activo', 'Fecha_Alta']
    ordering = ['Producto']


@admin.register(Pedido)
class PedidoAdmin(ERPModelAdmin):
    list_display = ['ID_Pedido', 'Fecha', 'Cliente', 'Total', 'Estado', 'Pago', 'Entregado']
    list_filter = ['Estado', 'Pago', 'Entregado', 'Fecha']
    search_fields = ['ID_Pedido', 'Cliente__Nombre', 'Cliente__Telefono']
    date_hierarchy = 'Fecha'
    ordering = ['-Fecha', '-ID_Pedido']
    readonly_fields = ['Creado_En']


@admin.register(DetallePedido)
class DetallePedidoAdmin(ERPModelAdmin):
    list_display = ['ID_Pedido', 'SKU', 'Peso', 'Precio', 'Descuento', 'Subtotal']
    search_fields = ['ID_Pedido__ID_Pedido', 'SKU__SKU', 'SKU__Producto']
    readonly_fields = ['Subtotal']


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(ERPModelAdmin):
    list_display = ['ID_Movimiento', 'SKU', 'Fecha', 'Debe', 'Haber', 'Comentario']
    list_filter = ['Fecha']
    search_fields = ['ID_Movimiento', 'SKU__SKU', 'Comentario']
    date_hierarchy = 'Fecha'
    ordering = ['-Fecha']


@admin.register(AsientoContable)
class AsientoContableAdmin(ERPModelAdmin):
    list_display = ['id', 'Fecha', 'Cuenta', 'Debe', 'Haber', 'Comentarios']
    list_filter = ['Fecha', 'Cuenta']
    search_fields = ['id', 'Comentarios']
    date_hierarchy = 'Fecha'


@admin.register(CatalogoCuenta)
class CatalogoCuentaAdmin(ERPModelAdmin):
    list_display = ['ID_Cuenta', 'Nombre', 'Tipo', 'Activo']
    list_filter = ['Tipo', 'Activo']
    search_fields = ['ID_Cuenta', 'Nombre']


@admin.register(Bitacora)
class BitacoraAdmin(ERPModelAdmin):
    list_display = ['ID_Bitacora', 'Fecha_Hora', 'Usuario', 'Tabla', 'Operacion', 'Registro_Clave']
    list_filter = ['Tabla', 'Operacion', 'Fecha_Hora']
    search_fields = ['Usuario', 'Tabla', 'Registro_Clave', 'Detalle']
    date_hierarchy = 'Fecha_Hora'
    readonly_fields = ['ID_Bitacora', 'Fecha_Hora', 'Usuario', 'Tabla',
                       'Operacion', 'Registro_Clave', 'Detalle']

    def has_add_permission(self, _request):
        return False

    def has_change_permission(self, _request, _obj=None):
        return False
