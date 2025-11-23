"""
Punto de entrada principal del bot
"""
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, ContextTypes
from telegram.error import BadRequest, TimedOut, NetworkError

# Aplicar nest_asyncio al inicio para permitir anidar event loops
# Esto es necesario para que los métodos síncronos puedan ejecutar código asíncrono
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass  # nest_asyncio no está instalado, pero no es crítico

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
            pass  # Si no podemos enviar el mensaje, simplemente ignoramos


def main():
    """Inicia el bot"""
    # Limpiar asociaciones incorrectas al iniciar
    cleanup_on_start()
    
    # Crear aplicación
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Registrar error handler
    application.add_error_handler(error_handler)
    
    # Registrar todos los handlers
    register_all_handlers(application)
    
    # Inicializar base de datos (crear tablas si no existen)
    print("📦 Inicializando base de datos...")
    asyncio.run(init_db())
    print("✅ Base de datos inicializada.")
    
    # Inicializar engine SQLAlchemy
    print("🔧 Inicializando SQLAlchemy engine...")
    asyncio.run(init_engine())
    print("✅ SQLAlchemy engine inicializado.")
    
    print("🤖 Bot médico iniciado...")
    print(f"👑 SuperAdmin ID: {SUPER_ADMIN_ID}")
    
    try:
        application.run_polling()
    finally:
        # Cerrar engine al finalizar
        print("🔒 Cerrando SQLAlchemy engine...")
        asyncio.run(close_engine())


if __name__ == "__main__":
    main()
