# 🚀 Configuración Rápida de Webhooks

## ✅ Archivos Creados

1. **`webhook_server.py`** - Servidor Flask para recibir webhooks
2. **`wsgi.py`** - Configuración WSGI para PythonAnywhere
3. **`scripts/setup_webhook.py`** - Script para configurar webhook
4. **`docs/PYTHONANYWHERE_WEBHOOK_SETUP.md`** - Guía completa

## 📋 Pasos Rápidos en PythonAnywhere

### 1. Clonar y Configurar

```bash
cd ~
git clone https://github.com/tu-usuario/gynsys.git
cd gynsys
python3.10 -m venv venv
source venv/bin/activate
pip install --user -r requirements.txt
```

### 2. Crear archivo `.env`

```bash
nano .env
```

Contenido:
```
BOT_TOKEN=tu_token
SUPER_ADMIN_ID=tu_id
ENCRYPTION_KEY=tu_clave
DB_PATH=database/medical_bot.db
```

### 3. Configurar Aplicación Web

1. Ir a pestaña **"Web"** en PythonAnywhere
2. Click **"Add a new web app"**
3. Seleccionar **Flask** y Python 3.10
4. Editar **WSGI configuration file** y pegar contenido de `wsgi.py` (ajustar ruta)
5. **Source code:** `/home/tu-usuario/gynsys`
6. **Working directory:** `/home/tu-usuario/gynsys`

### 4. Configurar Webhook

Opción A - Usando el endpoint:
```
https://tu-usuario.pythonanywhere.com/set_webhook?url=https://tu-usuario.pythonanywhere.com/webhook
```

Opción B - Usando el script:
```bash
python scripts/setup_webhook.py set https://tu-usuario.pythonanywhere.com/webhook
```

### 5. Verificar

- Health check: `https://tu-usuario.pythonanywhere.com/`
- Ver info webhook: `python scripts/setup_webhook.py info`
- Probar bot: Envía `/start` al bot

## 🔄 Actualizar Código

```bash
cd ~/gynsys
git pull origin main
source venv/bin/activate
pip install --user -r requirements.txt
```

Luego en PythonAnywhere Web → Click **"Reload"**

## 📚 Documentación Completa

Ver: `docs/PYTHONANYWHERE_WEBHOOK_SETUP.md`

