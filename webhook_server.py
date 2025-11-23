"""
Servidor webhook para el bot de Telegram en PythonAnywhere
"""
import logging
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, ContextTypes
from telegram.error import BadRequest, TimedOut, NetworkError

# Aplicar nest_asyncio para permitir anidar event loops
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

from config import BOT_TOKEN, SUPER_ADMIN_ID
from database.connection import init_db
from database.engine import init_engine, close_engine
from utils.startup import cleanup_on_start
from handlers.registration import register_all_handlers

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Crear aplicación Flask
app = Flask(__name__)

# Variable global para la aplicación del bot
bot_application = None


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja errores globales del bot"""
    logger.error(f"Exception while handling an update: {context.error}", exc_info=context.error)
    
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
            pass


def init_bot():
    """Inicializa la aplicación del bot"""
    global bot_application
    
    if bot_application is not None:
        return bot_application
    
    logger.info("Inicializando bot...")
    
    # Limpiar asociaciones incorrectas al iniciar
    cleanup_on_start()
    
    # Crear aplicación
    bot_application = Application.builder().token(BOT_TOKEN).build()
    
    # Registrar error handler
    bot_application.add_error_handler(error_handler)
    
    # Registrar todos los handlers
    register_all_handlers(bot_application)
    
    # Inicializar base de datos
    logger.info("Inicializando base de datos...")
    asyncio.run(init_db())
    logger.info("Base de datos inicializada.")
    
    # Inicializar engine SQLAlchemy
    logger.info("Inicializando SQLAlchemy engine...")
    asyncio.run(init_engine())
    logger.info("SQLAlchemy engine inicializado.")
    
    logger.info("Bot inicializado correctamente.")
    return bot_application


@app.route('/', methods=['GET'])
def index():
    """Endpoint de salud"""
    return jsonify({
        "status": "ok",
        "service": "GynSys Bot Webhook",
        "superadmin_id": SUPER_ADMIN_ID
    }), 200


@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint para recibir updates de Telegram"""
    try:
        # Asegurar que el bot esté inicializado
        ensure_bot_initialized()
        
        # Obtener el update del request
        update_data = request.get_json()
        
        if not update_data:
            logger.warning("Request sin datos JSON")
            return jsonify({"ok": False, "error": "No data"}), 400
        
        # Crear objeto Update
        update = Update.de_json(update_data, bot_application.bot)
        
        # Procesar el update de forma asíncrona
        # Usar create_task para no bloquear
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(bot_application.process_update(update))
        
        return jsonify({"ok": True}), 200
        
    except Exception as e:
        logger.error(f"Error procesando webhook: {e}", exc_info=True)
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    """Endpoint para configurar el webhook en Telegram"""
    from telegram import Bot
    
    webhook_url = request.args.get('url') or request.form.get('url')
    
    if not webhook_url:
        return jsonify({
            "error": "URL requerida",
            "usage": "/set_webhook?url=https://tu-usuario.pythonanywhere.com/webhook"
        }), 400
    
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Obtener o crear event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(bot.set_webhook(url=webhook_url))
        
        return jsonify({
            "ok": True,
            "webhook_url": webhook_url,
            "result": result
        }), 200
    except Exception as e:
        logger.error(f"Error configurando webhook: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/delete_webhook', methods=['GET', 'POST'])
def delete_webhook():
    """Endpoint para eliminar el webhook"""
    from telegram import Bot
    
    try:
        bot = Bot(token=BOT_TOKEN)
        
        # Obtener o crear event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(bot.delete_webhook())
        
        return jsonify({
            "ok": True,
            "result": result
        }), 200
    except Exception as e:
        logger.error(f"Error eliminando webhook: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


# Inicializar bot de forma lazy (solo cuando se necesite)
# Esto evita problemas de inicialización en PythonAnywhere
def ensure_bot_initialized():
    """Asegura que el bot esté inicializado"""
    global bot_application
    if bot_application is None:
        init_bot()
    return bot_application


@app.route('/health', methods=['GET'])
def health():
    """Endpoint de salud detallado"""
    try:
        ensure_bot_initialized()
        return jsonify({
            "status": "ok",
            "service": "GynSys Bot Webhook",
            "superadmin_id": SUPER_ADMIN_ID,
            "bot_initialized": bot_application is not None
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


# Inicializar bot al cargar el módulo (solo en desarrollo local)
if __name__ == '__main__':
    # Para desarrollo local
    init_bot()
    app.run(host='0.0.0.0', port=5000, debug=False)
# En PythonAnywhere, la inicialización será lazy (cuando llegue el primer webhook)

