# 🚀 Guía para Ejecutar el Bot Localmente

Esta guía te ayudará a ejecutar el bot de Telegram en tu máquina local para desarrollo y pruebas antes de desplegar a producción.

## 📋 Prerrequisitos

1. **Python 3.8+** instalado
2. **Git** instalado
3. **Token del Bot de Telegram** (obtener de [@BotFather](https://t.me/BotFather))
4. **Tu Telegram ID** (obtener de [@userinfobot](https://t.me/userinfobot))

## 🔧 Configuración Inicial

### 1. Clonar el Repositorio (si aún no lo tienes)

```bash
git clone https://github.com/gynsys/gynsys.git
cd gynsys
```

### 2. Crear Entorno Virtual

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
# Token del bot de Telegram (obtener de @BotFather)
BOT_TOKEN=tu_token_aqui

# Tu Telegram ID (obtener de @userinfobot)
SUPER_ADMIN_ID=tu_telegram_id_aqui

# Ruta de la base de datos (opcional, por defecto: database/medical_bot.db)
DB_PATH=database/medical_bot.db

# Clave de cifrado (generar con el comando de abajo)
ENCRYPTION_KEY=tu_clave_de_cifrado_aqui

# Logs del sistema (opcional, por defecto: True)
LOGS_SYS=True
```

#### Generar Clave de Cifrado

Ejecuta este comando para generar una clave de cifrado segura:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode('utf-8'))"
```

Copia el resultado y pégalo en `ENCRYPTION_KEY` en tu archivo `.env`.

### 5. Crear Directorio de Base de Datos

```bash
mkdir -p database
```

## ▶️ Ejecutar el Bot

### Modo Desarrollo (Polling)

Para ejecutar el bot en modo desarrollo local, simplemente ejecuta:

```bash
python main.py
```

El bot iniciará y comenzará a recibir mensajes usando **polling** (el bot consulta constantemente a Telegram por nuevos mensajes).

**Ventajas del modo polling:**
- ✅ Fácil de configurar
- ✅ No requiere servidor web
- ✅ Ideal para desarrollo y pruebas
- ✅ Funciona detrás de un firewall/NAT

**Desventajas:**
- ⚠️ Menos eficiente que webhooks
- ⚠️ No recomendado para producción con muchos usuarios

### Verificar que Funciona

1. Abre Telegram y busca tu bot
2. Envía `/start` al bot
3. Deberías recibir una respuesta del bot

## 🔄 Despliegue por Etapas

### Etapa 1: Desarrollo Local
- ✅ Ejecutar con `python main.py` (polling)
- ✅ Probar todas las funcionalidades
- ✅ Verificar logs en consola
- ⚠️ **IMPORTANTE:** Si el bot tiene webhook activo en producción, desactívalo primero (ver [BOT_TOKEN_MULTIPLE_ENVS.md](BOT_TOKEN_MULTIPLE_ENVS.md))

### Etapa 2: Staging/Pruebas
- ✅ Desplegar en servidor de pruebas (PythonAnywhere, Heroku, etc.)
- ✅ Usar webhooks (`webhook_server.py`)
- ✅ Probar con usuarios de prueba
- 💡 **Recomendación:** Usa un bot de desarrollo separado para no afectar producción

### Etapa 3: Producción
- ✅ Desplegar en servidor de producción
- ✅ Configurar webhooks
- ✅ Monitorear logs y errores

## ⚠️ Importante: Token del Bot

**NO puedes usar el mismo token simultáneamente en producción y local.**

Ver la guía completa: [BOT_TOKEN_MULTIPLE_ENVS.md](BOT_TOKEN_MULTIPLE_ENVS.md)

**Solución rápida:**
- **Opción 1 (Recomendado):** Crear un bot de desarrollo separado
- **Opción 2:** Desactivar webhook antes de probar localmente:
  ```powershell
  .\scripts\toggle_webhook.ps1 off
  ```

## 🐛 Solución de Problemas

### Error: "BOT_TOKEN no está configurado"
- Verifica que el archivo `.env` existe y contiene `BOT_TOKEN`
- Asegúrate de que el token es correcto (sin espacios extra)

### Error: "SUPER_ADMIN_ID no está configurado"
- Verifica que el archivo `.env` contiene `SUPER_ADMIN_ID`
- Asegúrate de que es un número (sin comillas)

### Error: "ENCRYPTION_KEY no está configurado"
- Genera una nueva clave con el comando proporcionado
- Asegúrate de que la clave está en el archivo `.env`

### Error: "ModuleNotFoundError"
- Activa el entorno virtual: `.\venv\Scripts\Activate.ps1` (Windows) o `source venv/bin/activate` (Linux/Mac)
- Instala las dependencias: `pip install -r requirements.txt`

### El bot no responde
- Verifica que el bot está corriendo (deberías ver logs en consola)
- Verifica que el token es correcto
- Verifica que no hay errores en los logs

## 📝 Logs

Los logs se muestran en la consola cuando ejecutas el bot. Para ver más detalles, puedes cambiar el nivel de logging en `main.py`:

```python
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Cambiar de INFO a DEBUG para más detalles
)
```

## 🔐 Seguridad

⚠️ **IMPORTANTE:**
- **NUNCA** subas el archivo `.env` a Git
- El archivo `.env` ya está en `.gitignore`
- No compartas tu `BOT_TOKEN` o `ENCRYPTION_KEY`
- En producción, usa variables de entorno del sistema o un gestor de secretos

## 📚 Recursos Adicionales

- [Documentación de python-telegram-bot](https://python-telegram-bot.org/)
- [Guía de Webhooks](docs/PYTHONANYWHERE_WEBHOOK_SETUP.md)
- [Guía de Git y GitHub](docs/GIT_GITHUB_SETUP.md)

