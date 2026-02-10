"""
Punto de entrada principal del bot
Soporta dos modos:
- Polling: Para desarrollo local (WEBHOOK=OFF)
- Webhook: Para producción (WEBHOOK=ON)
"""

import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, ContextTypes
from telegram.error import BadRequest, TimedOut, NetworkError

# Aplicar nest_asyncio al inicio para permitir anidar event loops
# Esto es necesario para que los métodos síncronos puedan ejecutar código asíncrono
# try:
#     import nest_asyncio
#     nest_asyncio.apply()
# except ImportError:
#     pass  # nest_asyncio no está instalado, pero no es crítico

from config import BOT_TOKEN, SUPER_ADMIN_ID, WEBHOOK, WEBHOOK_URL, WEBHOOK_PORT
from database.connection import init_db
from database.engine import init_engine, close_engine
from utils.startup import cleanup_on_start
from handlers.registration import register_all_handlers
from utils.health_metrics import get_metrics

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# os.chdir('/home/pablopem/gynsys')  # Comentado para producción

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja errores globales del bot"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
    # Registrar error en métricas
    metrics = get_metrics()
    error_type = type(context.error).__name__
    metrics.log_error(error_type)

    # Manejar errores específicos
    if isinstance(context.error, BadRequest):
        error_msg = str(context.error).lower()
        if "query is too old" in error_msg or "query id is invalid" in error_msg:
            logger.warning("Callback query expirado, ignorando error")
            return
        elif "message to edit not found" in error_msg or "no text" in error_msg:
            logger.warning("Mensaje no encontrado para editar, ignorando error")
            return

    if isinstance(context.error, (TimedOut, NetworkError)):
        logger.warning(f"Error de red/timeout: {context.error}")
        return

    # Para otros errores, intentar notificar al usuario si es posible
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Ocurrió un error inesperado. Por favor, intenta nuevamente."
            )
        except Exception:
            pass  # Si no podemos enviar el mensaje, simplemente ignoramos


def run_polling_mode(application: Application):
    """Ejecuta el bot en modo polling (desarrollo local)"""
    print("🤖 Bot médico iniciado en modo POLLING...")
    print(f"👑 SuperAdmin ID: {SUPER_ADMIN_ID}")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(application.initialize())
        application.run_polling(close_loop=False)
    finally:
        try:
            print("🔒 Cerrando SQLAlchemy engine...")
            asyncio.run(close_engine())
        finally:
            loop.close()
            asyncio.set_event_loop(None)


def run_webhook_mode(application: Application):
    """Ejecuta el bot en modo webhook (producción)"""
    try:
        from flask import Flask, request, jsonify
    except ImportError:
        raise ImportError("Flask no está instalado. Instálalo con: pip install flask")

    if not WEBHOOK_URL:
        raise ValueError("WEBHOOK_URL debe estar configurado cuando WEBHOOK=ON")

    # Crear aplicación Flask
    flask_app = Flask(__name__)

    # Inicializar la aplicación del bot (necesario para webhooks)
    print("🔧 Inicializando Application para webhook...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(application.initialize())
    print("✅ Application inicializada.")

    @flask_app.route('/', methods=['GET'])
    def index():
        """Endpoint de salud"""
        return jsonify({
            "status": "ok",
            "service": "GynSys Bot Webhook",
            "superadmin_id": SUPER_ADMIN_ID,
            "mode": "webhook"
        }), 200
    
    @flask_app.route('/health', methods=['GET'])
    def health():
        """Endpoint de métricas de salud del bot"""
        metrics = get_metrics()
        return jsonify(metrics.get_metrics()), 200

    @flask_app.route('/webhook', methods=['POST'])
    def webhook():
        """Endpoint para recibir updates de Telegram"""
        try:
            update_data = request.get_json()
            if not update_data:
                return jsonify({"ok": False, "error": "No data"}), 400

            # Crear objeto Update y procesarlo
            update = Update.de_json(update_data, application.bot)
            loop.run_until_complete(application.process_update(update))
            return jsonify({"ok": True}), 200
        except Exception as e:
            logger.error(f"Error procesando webhook: {e}", exc_info=True)
            return jsonify({"ok": False, "error": str(e)}), 500

    @flask_app.route('/set_webhook', methods=['POST'])
    def set_webhook():
        """Endpoint para configurar el webhook"""
        try:
            loop.run_until_complete(application.bot.set_webhook(url=WEBHOOK_URL))
            return jsonify({"ok": True, "webhook_url": WEBHOOK_URL}), 200
        except Exception as e:
            logger.error(f"Error configurando webhook: {e}", exc_info=True)
            return jsonify({"ok": False, "error": str(e)}), 500

    @flask_app.route('/delete_webhook', methods=['POST'])
    def delete_webhook():
        """Endpoint para eliminar el webhook"""
        try:
            loop.run_until_complete(application.bot.delete_webhook())
            return jsonify({"ok": True}), 200
        except Exception as e:
            logger.error(f"Error eliminando webhook: {e}", exc_info=True)
            return jsonify({"ok": False, "error": str(e)}), 500

    print("🤖 Bot médico iniciado en modo WEBHOOK...")
    print(f"👑 SuperAdmin ID: {SUPER_ADMIN_ID}")
    print(f"🌐 Webhook URL: {WEBHOOK_URL}")
    print(f"🔌 Puerto: {WEBHOOK_PORT}")

    # Configurar webhook automáticamente al iniciar
    try:
        print("🔗 Configurando webhook...")
        loop.run_until_complete(application.bot.set_webhook(url=WEBHOOK_URL))
        print("✅ Webhook configurado correctamente.")
    except Exception as e:
        logger.error(f"Error configurando webhook: {e}", exc_info=True)
        print("⚠️ No se pudo configurar el webhook automáticamente.")

    # Iniciar servidor Flask
    flask_app.run(host='0.0.0.0', port=WEBHOOK_PORT, debug=False)


def main():
    """Inicia el bot en modo polling o webhook según configuración"""
    # Limpiar asociaciones incorrectas al iniciar
    cleanup_on_start()

    # Crear aplicación
    application = Application.builder().token(BOT_TOKEN).build()

    # Registrar error handler
    application.add_error_handler(error_handler)

    # Registrar todos los handlers
    register_all_handlers(application)
    #application.add_handler(CallbackQueryHandler(_all_callbacks), group=2)

    # Inicializar base de datos (crear tablas si no existen)
    print("📦 Inicializando base de datos...")
    asyncio.run(init_db())
    print("✅ Base de datos inicializada.")

    # Inicializar engine SQLAlchemy
    print("🔧 Inicializando SQLAlchemy engine...")
    asyncio.run(init_engine())
    print("✅ SQLAlchemy engine inicializado.")
    
    # Inicializar métricas de salud
    print("📊 Inicializando sistema de métricas de salud...")
    metrics = get_metrics()
    print(f"✅ Métricas inicializadas. Estado: {metrics.get_health_status()}")

    # Ejecutar en modo polling o webhook según configuración
    if WEBHOOK == 'ON':
        run_webhook_mode(application)
    else:
        run_polling_mode(application)


if __name__ == "__main__":
    main()
