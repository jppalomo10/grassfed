# Guía de despliegue — GrassFed ERP

Stack: Django 5 · MySQL 8 · Gunicorn · Nginx · Oracle Cloud (Ubuntu) · Let's Encrypt

---

## 1. Preparar el repositorio local (una sola vez)

```bash
git init
git add .
git commit -m "Initial commit"
```

Crear el repositorio en GitHub (sin README ni .gitignore, que ya tienes), luego:

```bash
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git branch -M main
git push -u origin main
```

> El archivo `.env` **no viaja a GitHub** (está en `.gitignore`). En el servidor lo creas manualmente.

---

## 2. Configurar el servidor Oracle (una sola vez)

### 2.1 Conectarse al servidor

```bash
ssh ubuntu@IP_DEL_SERVIDOR
```

### 2.2 Instalar dependencias del sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git
```

MySQL 8 ya debe estar instalado. Si no:

```bash
sudo apt install -y mysql-server
sudo mysql_secure_installation
```

### 2.3 Clonar el proyecto

```bash
cd /var/www
sudo git clone https://github.com/TU_USUARIO/TU_REPO.git grassfed
sudo chown -R ubuntu:ubuntu /var/www/grassfed
cd /var/www/grassfed
```

### 2.4 Crear entorno virtual e instalar dependencias

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### 2.5 Crear el archivo `.env` en el servidor

```bash
nano .env
```

Contenido (ajusta los valores):

```
SECRET_KEY=genera-una-clave-larga-aqui-minimo-50-caracteres
DEBUG=False
ALLOWED_HOSTS=erp.tudominio.com

DB_NAME=grassfed_erp
DB_HOST=localhost
DB_PORT=3306
DB_DEV_USER=TU_USUARIO_MYSQL
DB_DEV_PASSWORD=TU_CONTRASEÑA_MYSQL
```

Para generar el `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(60))"
```

### 2.6 Crear las tablas de Django en MySQL

```bash
source .venv/bin/activate
python manage.py migrate
```

### 2.7 Recolectar archivos estáticos

```bash
python manage.py collectstatic --noinput
```

### 2.8 Marcar tu usuario como superusuario de Django

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
u = User.objects.get(username='TU_USUARIO_MYSQL')
u.is_staff = True
u.is_superuser = True
u.save()
exit()
```

---

## 3. Configurar Gunicorn como servicio (una sola vez)

```bash
sudo nano /etc/systemd/system/grassfed.service
```

```ini
[Unit]
Description=GrassFed ERP (Gunicorn)
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/var/www/grassfed
ExecStart=/var/www/grassfed/.venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/run/grassfed.sock \
          erp_project.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable grassfed
sudo systemctl start grassfed
```

---

## 4. Configurar Nginx + subdominio (una sola vez)

### 4.1 Apuntar el subdominio a tu servidor

En el panel DNS de tu proveedor de dominio, agrega un registro:

| Tipo | Nombre | Valor            | TTL  |
|------|--------|------------------|------|
| A    | erp    | IP_DEL_SERVIDOR  | 3600 |

Espera unos minutos a que propague. Puedes verificar con:

```bash
nslookup erp.tudominio.com
```

### 4.2 Crear el bloque Nginx

```bash
sudo nano /etc/nginx/sites-available/grassfed
```

```nginx
server {
    listen 80;
    server_name erp.tudominio.com;

    location /static/ {
        alias /var/www/grassfed/staticfiles/;
    }

    location / {
        proxy_pass http://unix:/run/grassfed.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/grassfed /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4.3 Activar HTTPS con Let's Encrypt

```bash
sudo certbot --nginx -d erp.tudominio.com
```

Certbot modifica el bloque Nginx automáticamente y renueva el certificado solo. Verifica la renovación automática:

```bash
sudo certbot renew --dry-run
```

### 4.4 Abrir los puertos en Oracle Cloud

En la consola de Oracle Cloud → **Networking → Virtual Cloud Networks → Security Lists**, agrega reglas de entrada:

| Puerto | Protocolo | Origen    |
|--------|-----------|-----------|
| 80     | TCP       | 0.0.0.0/0 |
| 443    | TCP       | 0.0.0.0/0 |

También en el firewall del servidor:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

---

## 5. Actualizar el servidor tras un push (uso recurrente)

```bash
# Local: subir cambios
git add .
git commit -m "descripción del cambio"
git push
```

```bash
# Servidor: bajar cambios y reiniciar
ssh ubuntu@IP_DEL_SERVIDOR
cd /var/www/grassfed
git pull
source .venv/bin/activate
pip install -r requirements.txt   # solo si cambió requirements.txt
python manage.py migrate          # solo si hay migraciones nuevas
python manage.py collectstatic --noinput
sudo systemctl restart grassfed
```

---

## 6. Comandos útiles en el servidor

```bash
# Ver logs de la aplicación
sudo journalctl -u grassfed -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log

# Reiniciar servicios
sudo systemctl restart grassfed
sudo systemctl reload nginx

# Estado del servicio
sudo systemctl status grassfed
```
