# GrassFed ERP

Aplicación web ERP para distribuidora de carnes, construida con **Django 5.2** y conectada a una base de datos **MySQL/MariaDB** existente (`grassfed_erp`). Desarrollada para la presentación del Proyecto Final de Bases de Datos — UFM 2026.

---

## Requisitos previos

| Herramienta | Versión mínima |
|-------------|---------------|
| Python | 3.10+ |
| pip | 23+ |
| MySQL / MariaDB | 8.0+ |
| Base de datos `grassfed_erp` | cargada con los scripts de `contexto_db/` |

---

## Instalación

### 1. Clonar / descargar el proyecto

```bash
git clone <url-del-repo>
cd Proyecto_Final
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/Mac
```

Edite `.env` y complete las contraseñas de los usuarios MySQL:

```env
SECRET_KEY=cambie-esto-por-una-clave-larga-y-aleatoria
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=grassfed_erp
DB_HOST=localhost
DB_PORT=3306

DB_DEV_USER=juan_dev
DB_DEV_PASSWORD=DevPass2026!

DB_ADMIN_USER=maria_admin
DB_ADMIN_PASSWORD=AdminPass2026!

DB_USER_USER=pedro_user
DB_USER_PASSWORD=UserPass2026!
```

> Las contraseñas reales están en `contexto_db/05_dcl_users_roles.sql`.

### 4. Crear tablas de Django (SQLite)

```bash
python manage.py migrate
```

> Esto solo crea las tablas internas de Django (usuarios, sesiones, admin) en `db.sqlite3`.  
> **No modifica** la base de datos MySQL existente.

### 5. Crear usuarios ERP de Django

```bash
python manage.py crear_usuarios
```

El comando crea tres usuarios Django vinculados a los tres roles MySQL:

| Usuario Django | Contraseña       | Rol       | Conexión MySQL |
|---------------|-----------------|-----------|---------------|
| `dev_user`    | (desde .env)    | dev       | `juan_dev`     |
| `admin_user`  | (desde .env)    | admin     | `maria_admin`  |
| `operador`    | (desde .env)    | usuario   | `pedro_user`   |

Si las variables `DB_*_PASSWORD` están en `.env`, se usan como contraseñas automáticamente. De lo contrario, el comando las solicita interactivamente.

### 6. Ejecutar el servidor

```bash
python manage.py runserver
```

Abrir en el navegador: **http://localhost:8000**

---

## Módulos disponibles

| Módulo | URL | Roles |
|--------|-----|-------|
| Dashboard | `/` | Todos |
| Clientes | `/clientes/` | Todos (editar: admin/dev) |
| Productos + Stock | `/productos/` | Todos |
| Pedidos | `/pedidos/` | Todos (cambiar estado: admin/dev) |
| Reportes | `/reportes/` | admin, dev |
| Consola SQL | `/dev/console/` | dev |
| Django Admin | `/admin/` | Superusuario |

---

## Arquitectura de base de datos

```
Django (SQLite)          MySQL grassfed_erp
─────────────────        ─────────────────────────────────────────
auth_user (dev_user) ──► juan_dev   → dev_role   (ALL privileges)
auth_user (admin_user)──► maria_admin → admin_role (SELECT + UPDATE limitado)
auth_user (operador) ──► pedro_user  → user_role  (SELECT + INSERT limitado)
```

Todas las consultas ERP viajan por el alias MySQL correspondiente al rol del usuario autenticado, demostrando el control de acceso a nivel de base de datos.

---

## Características destacadas para la presentación

- **Vistas SQL**: todos los reportes usan `vw_StockActual`, `vw_PendientesDePago`, `vw_VentasPorProducto`, etc.
- **Procedimientos almacenados**: creación de pedidos via `sp_RegistrarPedido` (JSON), anulación via `sp_AnularPedido`
- **Funciones SQL**: stock en tiempo real (`fn_StockProducto`), deuda del cliente (`fn_DeudaCliente`)
- **Triggers**: validación de stock (BEFORE INSERT), sincronización de totales (AFTER INSERT/UPDATE/DELETE), auditoría automática (6 triggers de bitácora)
- **Columna generada**: `DetallePedido.Subtotal` calculada por MySQL (`Peso * Precio - Descuento`)
- **Roles MySQL**: 3 conexiones distintas, permisos verificados en tiempo real por la BD
- **Exportación CSV**: todos los reportes con un clic
- **Factura imprimible**: vista de impresión limpia sin sidebar

---

## Estructura del proyecto

```
Proyecto_Final/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── erp_project/        ← configuración Django
│   ├── settings.py
│   └── urls.py
├── core/               ← modelos, router, middleware, utilidades
│   ├── models.py       ← 9 tablas + 7 vistas (managed=False)
│   ├── db_router.py    ← enrutador de base de datos por rol
│   ├── middleware.py   ← selecciona conexión MySQL por grupo
│   └── utils.py        ← call_procedure, export_csv, friendly_db_error
├── accounts/           ← login / logout / crear_usuarios
├── dashboard/          ← KPIs y últimos pedidos
├── clientes/           ← CRUD de clientes
├── productos/          ← catálogo + stock en tiempo real
├── pedidos/            ← CRUD pedidos + sp_RegistrarPedido
├── reportes/           ← 7 reportes + CSV + factura
└── dev/                ← consola SQL (solo SELECT)
```

---

## Comandos útiles

```bash
# Verificar configuración
python manage.py check

# Recolectar archivos estáticos (producción)
python manage.py collectstatic

# Crear superusuario para Django Admin
python manage.py createsuperuser
```
