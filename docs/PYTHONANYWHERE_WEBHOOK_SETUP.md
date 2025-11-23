# 🚀 Configuración de Webhooks en PythonAnywhere

## 📋 Requisitos Previos

- ✅ Cuenta en PythonAnywhere (plan gratuito o pagado)
- ✅ Bot de Telegram creado y token obtenido
- ✅ Repositorio en GitHub: `https://github.com/gynsys/gynsys.git`

---

## 🔧 Paso 1: Clonar Repositorio en PythonAnywhere

### En la Consola de PythonAnywhere (Bash):

```bash
cd ~
git clone https://github.com/gynsys/gynsys.git
cd gynsys
```

---

## 📦 Paso 2: Configurar Entorno Virtual

```bash
# Crear entorno virtual
python3.10 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install --user -r requirements.txt
```

**Nota:** En PythonAnywhere, a veces necesitas usar `pip install --user` para instalar paquetes.

---

## ⚙️ Paso 3: Configurar Variables de Entorno

```bash
# Crear archivo .env
nano .env
```

Agregar:
```
BOT_TOKEN=tu_token_aqui
SUPER_ADMIN_ID=tu_telegram_id
ENCRYPTION_KEY=tu_clave_de_encriptacion
DB_PATH=database/medical_bot.db
LOGS_SYS=True
```

Guardar: `Ctrl+O`, `Enter`, `Ctrl+X`

---

## 🌐 Paso 4: Configurar Aplicación Web en PythonAnywhere

### 4.1. Ir a la pestaña "Web"

1. Click en **"Add a new web app"**
2. Selecciona **"Flask"**
3. Python version: **3.10** (o la que tengas)
4. Path: `/home/tu-usuario/gynsys` (ajustar según tu usuario)

### 4.2. Editar el archivo WSGI

1. En la pestaña "Web", busca **"WSGI configuration file"**
2. Click para editarlo
3. Reemplazar todo el contenido con:

```python
import sys
import os

# Agregar el directorio del proyecto al path
path = '/home/tu-usuario/gynsys'  # CAMBIAR con tu usuario
if path not in sys.path:
    sys.path.insert(0, path)

# Cambiar al directorio del proyecto
os.chdir(path)

# Importar la aplicación Flask
from webhook_server import app

# Esta es la variable que PythonAnywhere busca
application = app
```

**⚠️ IMPORTANTE:** Reemplaza `tu-usuario` con tu usuario real de PythonAnywhere.

### 4.3. Configurar Source code y Working directory

En la pestaña "Web":
- **Source code:** `/home/tu-usuario/gynsys`
- **Working directory:** `/home/tu-usuario/gynsys`

---

## 🔗 Paso 5: Configurar Webhook en Telegram

### Opción A: Usando el Endpoint del Bot

1. Obtén tu URL de PythonAnywhere (ej: `https://tu-usuario.pythonanywhere.com`)
2. Ve a: `https://tu-usuario.pythonanywhere.com/set_webhook?url=https://tu-usuario.pythonanywhere.com/webhook`
3. O usa curl:
   ```bash
   curl https://tu-usuario.pythonanywhere.com/set_webhook?url=https://tu-usuario.pythonanywhere.com/webhook
   ```

### Opción B: Usando Python

```python
from telegram import Bot
import asyncio

BOT_TOKEN = "tu_token"
WEBHOOK_URL = "https://tu-usuario.pythonanywhere.com/webhook"

async def set_webhook():
    bot = Bot(token=BOT_TOKEN)
    result = await bot.set_webhook(url=WEBHOOK_URL)
    print(result)

asyncio.run(set_webhook())
```

### Opción C: Usando curl directamente a la API de Telegram

```bash
curl -X POST "https://api.telegram.org/botTU_TOKEN/setWebhook?url=https://tu-usuario.pythonanywhere.com/webhook"
```

---

## ✅ Paso 6: Verificar que Funciona

### 6.1. Verificar que la app está corriendo

Ve a: `https://tu-usuario.pythonanywhere.com/`

Deberías ver:
```json
{
  "status": "ok",
  "service": "GynSys Bot Webhook",
  "superadmin_id": 123456789
}
```

### 6.2. Verificar webhook configurado

```bash
curl https://api.telegram.org/botTU_TOKEN/getWebhookInfo
```

Deberías ver que el webhook está configurado con tu URL.

### 6.3. Probar el bot

Envía un mensaje `/start` al bot en Telegram. Debería responder.

---

## 🔍 Ver Logs

En PythonAnywhere:
1. Ve a la pestaña **"Tasks"** o **"Files"**
2. Busca el archivo de logs o usa:
   ```bash
   tail -f ~/gynsys/bot.log
   ```

O en la pestaña "Web" → "Error log" para ver errores de la aplicación web.

---

## 🔄 Actualizar Código

Cuando hagas cambios y los subas a GitHub:

```bash
cd ~/gynsys
git pull origin main
source venv/bin/activate
pip install --user -r requirements.txt
```

Luego, en la pestaña "Web" de PythonAnywhere, click en el botón **"Reload"** para reiniciar la aplicación.

---

## 🛠️ Troubleshooting

### El bot no responde

1. **Verificar que el webhook está configurado:**
   ```bash
   curl https://api.telegram.org/botTU_TOKEN/getWebhookInfo
   ```

2. **Verificar logs de error:**
   - Pestaña "Web" → "Error log"
   - O en consola: `tail -f ~/gynsys/bot.log`

3. **Verificar que la app está corriendo:**
   - Pestaña "Web" → Verificar que el estado es "Running"

### Error 500 en el webhook

- Revisar logs de error en PythonAnywhere
- Verificar que todas las variables de entorno están configuradas
- Verificar que la base de datos tiene permisos de escritura

### El webhook no se configura

- Verificar que la URL es accesible públicamente
- Verificar que usas HTTPS (requerido por Telegram)
- Verificar que el token del bot es correcto

---

## 📝 Notas Importantes

1. **PythonAnywhere Free Plan:**
   - Solo permite webhooks en el subdominio `.pythonanywhere.com`
   - La app se suspende después de inactividad (se reactiva automáticamente)

2. **PythonAnywhere Paid Plan:**
   - Permite dominios personalizados
   - La app está siempre activa

3. **Base de Datos:**
   - Asegúrate de que el directorio `database/` tiene permisos de escritura
   - Considera usar una base de datos externa para producción

4. **Variables de Entorno:**
   - En PythonAnywhere, también puedes configurar variables de entorno en la pestaña "Web" → "Environment variables"

---

## 🔗 URLs Importantes

- **Tu app:** `https://tu-usuario.pythonanywhere.com`
- **Webhook endpoint:** `https://tu-usuario.pythonanywhere.com/webhook`
- **Health check:** `https://tu-usuario.pythonanywhere.com/`
- **Configurar webhook:** `https://tu-usuario.pythonanywhere.com/set_webhook?url=https://tu-usuario.pythonanywhere.com/webhook`
- **Eliminar webhook:** `https://tu-usuario.pythonanywhere.com/delete_webhook`

---

## ✅ Checklist Final

- [ ] Repositorio clonado en PythonAnywhere
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas
- [ ] Archivo `.env` configurado
- [ ] Aplicación web Flask creada en PythonAnywhere
- [ ] Archivo WSGI configurado correctamente
- [ ] Webhook configurado en Telegram
- [ ] Bot responde a mensajes
- [ ] Logs funcionando correctamente

---

**¿Necesitas ayuda con algún paso específico?**

