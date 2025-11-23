# common/conversation_utils.py
import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest
from database import user_db
from common import texts
# Importamos el teclado del menú principal para ser autónomos
from features.main_menu.keyboards import get_main_menu_keyboard
logger = logging.getLogger(__name__)

async def cancel_and_show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Función universal y robusta para cancelar una conversación.
    Limpia todos los mensajes temporales y vuelve al menú principal.
    """
    query = update.callback_query
    chat_id = update.effective_chat.id

    # 1. Limpiar el mensaje principal de la conversación (el que se estaba editando)
    if main_conv_id := context.user_data.pop('main_conv_message_id', None):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=main_conv_id)
        except BadRequest:
            pass # Si ya no existe, no hay problema

    # 2. Limpiar el mensaje que inició la cancelación (/cancelar o el botón)
    if query:
        await query.answer("Operación cancelada.")
        # Simular un callback para volver al menú principal
        query.data = 'main_menu'
        # Importar aquí para evitar import circular
        from main import handle_all_callbacks
        await handle_all_callbacks(update, context)
    elif update.message:
        try:
            await update.message.delete()
        except BadRequest:
            pass
        # Enviar comando /start para volver al menú
        from main import start
        await start(update, context)

    # 3. Limpiar datos y terminar la conversación
    context.user_data.clear()
    return ConversationHandler.END

# Mantenemos la función antigua por si otro módulo la usa, pero la marcamos como obsoleta.
# Idealmente, deberíamos reemplazar todas las llamadas a 'cancel_conv' por la nueva función.
async def cancel_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.warning("'cancel_conv' es obsoleta y puede causar errores. Usar 'cancel_and_show_main_menu' en su lugar.")
    return await cancel_and_show_main_menu(update, context)