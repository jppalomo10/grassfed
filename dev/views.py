import re
from django.db import connections
from django.shortcuts import render

from core.decorators import role_required


# Only SELECT is allowed — no DDL/DML through the console
_SELECT_PATTERN = re.compile(r'^\s*SELECT\b', re.IGNORECASE)


@role_required('dev')
def sql_console(request):
    results = None
    columns = None
    error = None
    sql = ''
    row_count = 0

    if request.method == 'POST':
        sql = request.POST.get('sql', '').strip()
        if not sql:
            error = 'Ingrese una consulta SQL.'
        elif not _SELECT_PATTERN.match(sql):
            error = 'Solo se permiten consultas SELECT en la consola.'
        else:
            try:
                with connections['dev'].cursor() as cursor:
                    cursor.execute(sql)
                    columns = [col[0] for col in cursor.description]
                    results = cursor.fetchall()
                    row_count = len(results)
            except Exception as e:
                error = str(e)

    # Provide quick-run examples for the demo
    examples = [
        ('Stock actual', 'SELECT * FROM vw_StockActual ORDER BY Estado_Stock, SKU;'),
        ('Pendientes de pago', 'SELECT * FROM vw_PendientesDePago;'),
        ('Ventas por producto', 'SELECT * FROM vw_VentasPorProducto LIMIT 10;'),
        ('Ventas por cliente', 'SELECT * FROM vw_VentasPorCliente LIMIT 10;'),
        ('Bitácora reciente', 'SELECT * FROM Bitacora ORDER BY Fecha_Hora DESC LIMIT 20;'),
        ('Stock de un producto', "SELECT fn_StockProducto('CAR-LOM-01') AS stock_lb;"),
        ('Deuda de un cliente', "SELECT fn_DeudaCliente('50212345001') AS deuda_Q;"),
    ]

    return render(request, 'dev/console.html', {
        'sql': sql,
        'columns': columns,
        'results': results,
        'error': error,
        'row_count': row_count,
        'examples': examples,
    })
