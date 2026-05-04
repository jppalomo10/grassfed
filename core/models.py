from django.db import models


# ---------------------------------------------------------------------------
# Base tables
# ---------------------------------------------------------------------------

class CatalogoCuenta(models.Model):
    TIPO_CHOICES = [
        ('Activo', 'Activo'), ('Pasivo', 'Pasivo'), ('Patrimonio', 'Patrimonio'),
        ('Ingreso', 'Ingreso'), ('Gasto', 'Gasto'), ('Costo', 'Costo'),
    ]
    ID_Cuenta = models.CharField(max_length=20, primary_key=True)
    Nombre = models.CharField(max_length=150)
    Tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    Activo = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'CatalogoCuentas'
        verbose_name = 'Cuenta contable'
        verbose_name_plural = 'Catálogo de cuentas'

    def __str__(self):
        return f'{self.ID_Cuenta} — {self.Nombre}'


class Producto(models.Model):
    SKU = models.CharField(max_length=20, primary_key=True)
    Producto = models.CharField(max_length=120)
    Precio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    Stock_Minimo = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    Activo = models.BooleanField(default=True)
    Fecha_Alta = models.DateField()

    class Meta:
        managed = False
        db_table = 'Productos'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return f'{self.SKU} — {self.Producto}'


class Cliente(models.Model):
    Telefono = models.CharField(max_length=20, primary_key=True)
    Nombre = models.CharField(max_length=150)
    Direccion = models.CharField(max_length=255)
    Correo = models.CharField(max_length=120, null=True, blank=True)
    NIT = models.CharField(max_length=20, default='CF')
    Fecha_Alta = models.DateField()

    class Meta:
        managed = False
        db_table = 'Clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f'{self.Nombre} ({self.Telefono})'


# ---------------------------------------------------------------------------
# Transactional tables
# ---------------------------------------------------------------------------

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente de Pago', 'Pendiente de Pago'),
        ('Pagado', 'Pagado'),
        ('Anulado', 'Anulado'),
    ]
    PAGO_CHOICES = [
        ('Efectivo', 'Efectivo'),
        ('Transferencia', 'Transferencia'),
        ('Tarjeta', 'Tarjeta'),
    ]
    ID_Pedido = models.BigAutoField(primary_key=True)
    Fecha = models.DateField()
    Cliente = models.ForeignKey(
        Cliente, on_delete=models.RESTRICT,
        db_column='Cliente', to_field='Telefono', related_name='pedidos',
    )
    Total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    Estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='Pendiente de Pago')
    Pago = models.CharField(max_length=20, choices=PAGO_CHOICES)
    Envio = models.CharField(max_length=100, null=True, blank=True)
    Entregado = models.BooleanField(default=False)
    Creado_En = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'Pedidos'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-Fecha', '-ID_Pedido']

    def __str__(self):
        return f'Pedido #{self.ID_Pedido}'


class DetallePedido(models.Model):
    # Composite PK: ID_Pedido + SKU. Django requires one PK field;
    # inserts always use sp_RegistrarPedido, never ORM.save().
    ID_Pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE,
        db_column='ID_Pedido', primary_key=True, related_name='detalles',
    )
    SKU = models.ForeignKey(
        Producto, on_delete=models.RESTRICT,
        db_column='SKU', related_name='detalles',
    )
    Cantidad = models.IntegerField(null=True, blank=True)
    Peso = models.FloatField()
    Precio = models.DecimalField(max_digits=10, decimal_places=2)
    Descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # GENERATED ALWAYS AS STORED — MySQL calculates this; Django must not write it
    Subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)

    class Meta:
        managed = False
        db_table = 'DetallePedido'
        verbose_name = 'Línea de pedido'
        verbose_name_plural = 'Detalle de pedidos'

    def __str__(self):
        return f'Pedido #{self.ID_Pedido_id} / {self.SKU_id}'


class MovimientoInventario(models.Model):
    ID_Movimiento = models.CharField(max_length=30, primary_key=True)
    SKU = models.ForeignKey(
        Producto, on_delete=models.RESTRICT,
        db_column='SKU', related_name='movimientos',
    )
    Fecha = models.DateField()
    Debe = models.FloatField(null=True, blank=True)
    Haber = models.FloatField(null=True, blank=True)
    Comentario = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'MovimientosInventario'
        verbose_name = 'Movimiento de inventario'
        verbose_name_plural = 'Movimientos de inventario'
        ordering = ['-Fecha']

    def __str__(self):
        return self.ID_Movimiento


class InventarioHistorico(models.Model):
    Fecha = models.DateField(primary_key=True)
    SKU = models.ForeignKey(
        Producto, on_delete=models.RESTRICT,
        db_column='SKU', related_name='historico',
    )
    Peso = models.DecimalField(max_digits=10, decimal_places=3)

    class Meta:
        managed = False
        db_table = 'InventarioHistorico'
        verbose_name = 'Inventario histórico'
        verbose_name_plural = 'Inventario histórico'


class AsientoContable(models.Model):
    id = models.CharField(max_length=30, primary_key=True)
    Fecha = models.DateField()
    Cuenta = models.ForeignKey(
        CatalogoCuenta, on_delete=models.RESTRICT,
        db_column='Cuenta', related_name='asientos',
    )
    Debe = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    Haber = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    Comentarios = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'AsientosContables'
        verbose_name = 'Asiento contable'
        verbose_name_plural = 'Asientos contables'
        ordering = ['-Fecha']


class Bitacora(models.Model):
    OPERACION_CHOICES = [
        ('INSERT', 'INSERT'), ('UPDATE', 'UPDATE'), ('DELETE', 'DELETE'),
    ]
    ID_Bitacora = models.BigAutoField(primary_key=True)
    Fecha_Hora = models.DateTimeField(auto_now_add=True)
    Usuario = models.CharField(max_length=100)
    Tabla = models.CharField(max_length=50)
    Operacion = models.CharField(max_length=10, choices=OPERACION_CHOICES)
    Registro_Clave = models.CharField(max_length=100)
    Detalle = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'Bitacora'
        verbose_name = 'Entrada de bitácora'
        verbose_name_plural = 'Bitácora de auditoría'
        ordering = ['-Fecha_Hora']

    def __str__(self):
        return f'{self.Tabla} | {self.Operacion} | {self.Registro_Clave}'


# ---------------------------------------------------------------------------
# View-backed read-only models (backed by SQL VIEWs)
# ---------------------------------------------------------------------------

class VwStockActual(models.Model):
    SKU = models.CharField(max_length=20, primary_key=True)
    Producto = models.CharField(max_length=120)
    Stock_Minimo = models.DecimalField(max_digits=10, decimal_places=3)
    Ingresos_lb = models.FloatField()
    Transf_Salida_lb = models.FloatField()
    Ventas_lb = models.FloatField()
    Stock_lb = models.FloatField()
    Estado_Stock = models.CharField(max_length=10)  # OK / BAJO / AGOTADO

    class Meta:
        managed = False
        db_table = 'vw_StockActual'
        verbose_name = 'Stock actual'

    def __str__(self):
        return f'{self.SKU}: {self.Stock_lb} lb ({self.Estado_Stock})'


class VwPendienteDePago(models.Model):
    ID_Pedido = models.BigIntegerField(primary_key=True)
    Fecha = models.DateField()
    Dias_Vencimiento = models.IntegerField()
    Cliente = models.CharField(max_length=150)
    Telefono = models.CharField(max_length=20)
    Total = models.DecimalField(max_digits=12, decimal_places=2)
    Pago = models.CharField(max_length=20)
    Envio = models.CharField(max_length=100, null=True, blank=True)
    Entregado = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'vw_PendientesDePago'
        verbose_name = 'Pendiente de pago'


class VwPendienteDeEntrega(models.Model):
    ID_Pedido = models.BigIntegerField(primary_key=True)
    Fecha = models.DateField()
    Cliente = models.CharField(max_length=150)
    Telefono = models.CharField(max_length=20)
    Direccion = models.CharField(max_length=255)
    Total = models.DecimalField(max_digits=12, decimal_places=2)
    Envio = models.CharField(max_length=100, null=True, blank=True)
    Peso_Total_lb = models.FloatField()

    class Meta:
        managed = False
        db_table = 'vw_PendientesDeEntrega'
        verbose_name = 'Pendiente de entrega'


class VwVentaPorProducto(models.Model):
    SKU = models.CharField(max_length=20, primary_key=True)
    Producto = models.CharField(max_length=120)
    Num_Pedidos = models.IntegerField()
    Peso_Total_lb = models.FloatField()
    Total_Q = models.DecimalField(max_digits=12, decimal_places=2)
    Precio_Promedio = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'vw_VentasPorProducto'
        verbose_name = 'Ventas por producto'


class VwVentaPorCliente(models.Model):
    Telefono = models.CharField(max_length=20, primary_key=True)
    Nombre = models.CharField(max_length=150)
    NIT = models.CharField(max_length=20)
    Num_Pedidos = models.IntegerField()
    Total_Comprado_Q = models.DecimalField(max_digits=12, decimal_places=2)
    Deuda_Q = models.DecimalField(max_digits=12, decimal_places=2)
    Ultima_Compra = models.DateField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'vw_VentasPorCliente'
        verbose_name = 'Ventas por cliente'


class VwVentaPorFecha(models.Model):
    Fecha = models.DateField(primary_key=True)
    Num_Pedidos = models.IntegerField()
    Total_Q = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'vw_VentasPorFecha'
        verbose_name = 'Ventas por fecha'


class VwFacturaCompleta(models.Model):
    # View has rows per line item; ID_Pedido is not unique.
    # Always read with filter(ID_Pedido=x) — never save.
    ID_Pedido = models.BigIntegerField(primary_key=True)
    Fecha = models.DateField()
    Estado = models.CharField(max_length=30)
    Pago = models.CharField(max_length=20)
    Envio = models.CharField(max_length=100, null=True, blank=True)
    Entregado = models.BooleanField()
    Total = models.DecimalField(max_digits=12, decimal_places=2)
    Nombre_Cliente = models.CharField(max_length=150)
    Telefono_Cliente = models.CharField(max_length=20)
    NIT = models.CharField(max_length=20)
    Direccion = models.CharField(max_length=255)
    SKU = models.CharField(max_length=20)
    Producto = models.CharField(max_length=120)
    Cantidad = models.IntegerField(null=True, blank=True)
    Peso = models.FloatField()
    Precio = models.DecimalField(max_digits=10, decimal_places=2)
    Descuento = models.DecimalField(max_digits=10, decimal_places=2)
    Subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'vw_FacturaCompleta'
        verbose_name = 'Factura completa'
