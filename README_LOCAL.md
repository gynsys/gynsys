# 🚀 Ejecutar Bot Localmente - Guía Rápida

## Inicio Rápido

### Windows (PowerShell)
```powershell
.\scripts\run_local.ps1
```

### Linux/Mac
```bash
chmod +x scripts/run_local.sh
./scripts/run_local.sh
```

### Manual
```bash
# 1. Activar entorno virtual
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# 2. Ejecutar bot
python main.py
```

## Configuración Requerida

Crea un archivo `.env` en la raíz con:

```env
BOT_TOKEN=tu_token_de_@BotFather
SUPER_ADMIN_ID=tu_telegram_id_de_@userinfobot
ENCRYPTION_KEY=generar_con_comando_de_abajo
```

**Generar clave de cifrado:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode('utf-8'))"
```

## Documentación Completa

Ver [docs/EJECUTAR_LOCAL.md](docs/EJECUTAR_LOCAL.md) para la guía completa.

