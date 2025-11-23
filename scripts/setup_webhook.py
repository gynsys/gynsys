"""
Script para configurar el webhook en Telegram
Úsalo después de desplegar en PythonAnywhere
"""
import asyncio
import sys
from telegram import Bot
from config import BOT_TOKEN

async def set_webhook(url: str):
    """Configura el webhook en Telegram"""
    bot = Bot(token=BOT_TOKEN)
    
    print(f"🔗 Configurando webhook: {url}")
    result = await bot.set_webhook(url=url)
    
    # Verificar información del webhook
    webhook_info = await bot.get_webhook_info()
    
    print(f"\n✅ Webhook configurado:")
    print(f"   URL: {webhook_info.url}")
    print(f"   Pending updates: {webhook_info.pending_update_count}")
    print(f"   Last error: {webhook_info.last_error_message or 'None'}")
    
    return result

async def delete_webhook():
    """Elimina el webhook (vuelve a polling)"""
    bot = Bot(token=BOT_TOKEN)
    result = await bot.delete_webhook()
    print("✅ Webhook eliminado. El bot volverá a usar polling.")
    return result

async def get_webhook_info():
    """Obtiene información del webhook actual"""
    bot = Bot(token=BOT_TOKEN)
    info = await bot.get_webhook_info()
    
    print(f"\n📊 Información del Webhook:")
    print(f"   URL: {info.url or 'No configurado'}")
    print(f"   Pending updates: {info.pending_update_count}")
    print(f"   Last error date: {info.last_error_date or 'None'}")
    print(f"   Last error message: {info.last_error_message or 'None'}")
    print(f"   Max connections: {info.max_connections or 'None'}")
    
    return info

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python scripts/setup_webhook.py set <URL>  - Configurar webhook")
        print("  python scripts/setup_webhook.py delete     - Eliminar webhook")
        print("  python scripts/setup_webhook.py info       - Ver información del webhook")
        print("\nEjemplo:")
        print("  python scripts/setup_webhook.py set https://tu-usuario.pythonanywhere.com/webhook")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "set":
        if len(sys.argv) < 3:
            print("❌ Error: Se requiere una URL")
            print("Ejemplo: python scripts/setup_webhook.py set https://tu-usuario.pythonanywhere.com/webhook")
            sys.exit(1)
        url = sys.argv[2]
        asyncio.run(set_webhook(url))
    
    elif command == "delete":
        asyncio.run(delete_webhook())
    
    elif command == "info":
        asyncio.run(get_webhook_info())
    
    else:
        print(f"❌ Comando desconocido: {command}")
        sys.exit(1)

