# 🔑 Uso del Token del Bot en Múltiples Entornos

## ⚠️ Problema: Un Token, Múltiples Instancias

**NO puedes usar el mismo token de bot simultáneamente en producción y local** porque:

1. **Telegram solo permite una conexión activa por bot**
   - Si tienes un webhook configurado en producción, ese bot recibirá TODOS los mensajes
   - Si intentas usar polling en local con el mismo token, no recibirás mensajes (o habrá conflictos)

2. **Conflicto entre Webhook y Polling**
   - Webhook: Telegram envía mensajes a tu servidor
   - Polling: Tu servidor consulta a Telegram por mensajes
   - **No pueden coexistir** con el mismo token

## ✅ Soluciones

### Opción 1: Bot de Desarrollo Separado (Recomendado)

**Crear un bot de desarrollo con un token diferente:**

1. Habla con [@BotFather](https://t.me/BotFather) en Telegram
2. Envía `/newbot` o `/mybots` → selecciona tu bot → "API Token"
3. Crea un segundo bot para desarrollo: `/newbot` → "GynSys Dev" o similar
4. Obtén el token del bot de desarrollo

**Configuración:**

**Local (.env):**
```env
BOT_TOKEN=token_del_bot_de_desarrollo
SUPER_ADMIN_ID=tu_telegram_id
```

**Producción (variables de entorno del servidor):**
```env
BOT_TOKEN=token_del_bot_de_produccion
SUPER_ADMIN_ID=tu_telegram_id
```

**Ventajas:**
- ✅ Puedes probar sin afectar producción
- ✅ No necesitas desactivar webhooks
- ✅ Ambos bots pueden funcionar simultáneamente
- ✅ Ideal para desarrollo continuo

**Desventajas:**
- ⚠️ Tienes que mantener dos bots
- ⚠️ Los datos de desarrollo están separados

---

### Opción 2: Desactivar Webhook Temporalmente

**Cuando quieras probar localmente:**

1. **Eliminar webhook de producción:**
   ```bash
   # En el servidor de producción o desde local
   python scripts/setup_webhook.py delete
   ```

2. **Ejecutar bot localmente:**
   ```bash
   python main.py
   ```

3. **Cuando termines, reactivar webhook:**
   ```bash
   python scripts/setup_webhook.py set https://tu-servidor.pythonanywhere.com/webhook
   ```

**Ventajas:**
- ✅ Usas el mismo bot (mismos datos, mismos usuarios)
- ✅ No necesitas crear otro bot

**Desventajas:**
- ⚠️ El bot de producción queda inactivo mientras pruebas
- ⚠️ Proceso manual (fácil olvidarse de reactivar)
- ⚠️ Los usuarios no pueden usar el bot durante las pruebas

---

### Opción 3: Usar ngrok para Webhook Local (Avanzado)

**Exponer tu bot local como webhook temporalmente:**

1. **Instalar ngrok:**
   ```bash
   # Descargar de https://ngrok.com/
   # O con chocolatey (Windows)
   choco install ngrok
   ```

2. **Iniciar tu bot local con webhook:**
   ```bash
   # Terminal 1: Iniciar ngrok
   ngrok http 5000
   
   # Terminal 2: Iniciar bot local con webhook
   python webhook_server.py
   ```

3. **Configurar webhook con la URL de ngrok:**
   ```bash
   # Obtener la URL de ngrok (ej: https://abc123.ngrok.io)
   python scripts/setup_webhook.py set https://abc123.ngrok.io/webhook
   ```

**Ventajas:**
- ✅ Puedes probar webhooks localmente
- ✅ Mismo comportamiento que producción

**Desventajas:**
- ⚠️ Requiere ngrok (servicio externo)
- ⚠️ La URL cambia cada vez que reinicias ngrok
- ⚠️ Más complejo de configurar

---

## 🎯 Recomendación

**Para desarrollo diario:** Usa **Opción 1 (Bot de Desarrollo Separado)**
- Crea un bot de desarrollo
- Mantén ambos bots funcionando
- Prueba en desarrollo sin afectar producción

**Para pruebas puntuales en producción:** Usa **Opción 2 (Desactivar Webhook)**
- Solo cuando necesites probar con datos reales
- Recuerda reactivar el webhook después

**Para pruebas de webhooks:** Usa **Opción 3 (ngrok)**
- Solo si necesitas probar específicamente el comportamiento de webhooks

---

## 📝 Ejemplo de Configuración con Bot de Desarrollo

### Estructura de Archivos

```
gynsys/
├── .env                    # Bot de desarrollo (local)
├── .env.production         # Bot de producción (no subir a Git)
└── config.py               # Lee de .env automáticamente
```

### .env (Local - Desarrollo)
```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz_DEV
SUPER_ADMIN_ID=123456789
ENCRYPTION_KEY=tu_clave_dev
DB_PATH=database/medical_bot_dev.db
```

### .env.production (Producción - No subir a Git)
```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz_PROD
SUPER_ADMIN_ID=123456789
ENCRYPTION_KEY=tu_clave_prod
DB_PATH=database/medical_bot.db
```

### Script para Cambiar entre Entornos

**scripts/switch_env.ps1 (Windows):**
```powershell
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("dev", "prod")]
    [string]$Environment
)

if ($Environment -eq "dev") {
    Copy-Item .env .env.backup -ErrorAction SilentlyContinue
    Write-Host "✅ Cambiado a entorno de desarrollo" -ForegroundColor Green
} elseif ($Environment -eq "prod") {
    if (Test-Path .env.production) {
        Copy-Item .env .env.backup -ErrorAction SilentlyContinue
        Copy-Item .env.production .env
        Write-Host "✅ Cambiado a entorno de producción" -ForegroundColor Yellow
        Write-Host "⚠️  ADVERTENCIA: Estás usando el bot de producción!" -ForegroundColor Red
    } else {
        Write-Host "❌ No se encontró .env.production" -ForegroundColor Red
    }
}
```

---

## 🔐 Seguridad

⚠️ **IMPORTANTE:**
- **NUNCA** subas `.env` o `.env.production` a Git
- Ambos archivos ya están en `.gitignore`
- Usa variables de entorno en el servidor de producción
- No compartas tokens con nadie

---

## 📚 Recursos

- [Documentación de Telegram Bot API](https://core.telegram.org/bots/api)
- [Guía de Webhooks](docs/PYTHONANYWHERE_WEBHOOK_SETUP.md)
- [Guía de Ejecución Local](docs/EJECUTAR_LOCAL.md)

