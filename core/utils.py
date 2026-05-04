import csv
from django.db import connections
from django.http import HttpResponse
from core.db_router import _thread_locals


def get_db_alias():
    """Return the current request's MySQL database alias."""
    return getattr(_thread_locals, 'db_alias', 'dev')


def call_procedure(proc_name, args, db_alias=None):
    """
    Execute a MySQL stored procedure and return a list of result sets.
    Each result set is a list of tuples.
    """
    alias = db_alias or get_db_alias()
    results = []
    with connections[alias].cursor() as cursor:
        placeholders = ', '.join(['%s'] * len(args))
        cursor.execute(f'CALL {proc_name}({placeholders})', args)
        while True:
            if cursor.description:
                results.append(cursor.fetchall())
            if not cursor.nextset():
                break
    return results


def call_function(func_name, args, db_alias=None):
    """Call a MySQL scalar function and return its single return value."""
    alias = db_alias or get_db_alias()
    with connections[alias].cursor() as cursor:
        placeholders = ', '.join(['%s'] * len(args))
        cursor.execute(f'SELECT {func_name}({placeholders})', args)
        row = cursor.fetchone()
        return row[0] if row else None


def raw_query(sql, params=None, db_alias=None):
    """Execute a raw SELECT and return (columns, rows)."""
    alias = db_alias or get_db_alias()
    with connections[alias].cursor() as cursor:
        cursor.execute(sql, params or [])
        columns = [col[0] for col in (cursor.description or [])]
        rows = cursor.fetchall()
    return columns, rows


def export_csv(rows, filename, column_names):
    """
    Return an HttpResponse with CSV content.
    `rows` may be a queryset (ORM) or a list of tuples (raw cursor).
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    response.write('﻿')  # BOM for Excel compatibility
    writer = csv.writer(response)
    writer.writerow(column_names)
    for row in rows:
        if hasattr(row, '_meta'):
            # ORM instance
            writer.writerow([getattr(row, col) for col in column_names])
        else:
            # Raw tuple from cursor
            writer.writerow(row)
    return response


def friendly_db_error(exc):
    """
    Convert a MySQLdb exception into a user-friendly Spanish message.
    MySQL custom signals (SQLSTATE 45000) carry the message in the exception text.
    """
    msg = str(exc)
    # Custom SIGNAL from triggers (stock validation, etc.)
    if '45000' in msg or 'SIGNAL' in msg:
        # Extract the message text between single quotes if present
        parts = msg.split("'")
        if len(parts) >= 2:
            return parts[-2]
        return 'Error de validación en la base de datos.'
    if 'Duplicate entry' in msg:
        return 'Ya existe un registro con ese identificador.'
    if 'foreign key constraint' in msg.lower():
        return 'No se puede eliminar: el registro tiene datos relacionados.'
    if 'cannot be null' in msg.lower() or 'doesn\'t have a default' in msg.lower():
        return 'Faltan datos obligatorios.'
    if 'Data too long' in msg:
        return 'Uno de los campos excede el tamaño máximo permitido.'
    if 'Out of range' in msg:
        return 'Un valor numérico está fuera del rango permitido.'
    if 'Access denied' in msg:
        return 'Su rol no tiene permiso para realizar esta operación.'
    return f'Error en la base de datos: {msg[:200]}'
