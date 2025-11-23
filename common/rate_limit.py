# utils/rate_limit.py
import time
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database
import logging

logger = logging.getLogger(__name__)

ACTION_COOLDOWNS = {
    'agendar_cita': 86400,  # 24 horas
    'realizar_test': 604800 # 7 días
}

def rate_limit(action_key: str):
    """
    Decorador que previene que un usuario realice una acción clave demasiado rápido,
    ignorando el límite si el usuario es el administrador del bot.
    """
    def decorator(func):
        @wraps(func)
        async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            bot_id = context.bot_data.get('bot_db_id')

            if not bot_id:
                logger.error("Error en rate_limit: No se pudo obtener bot_db_id del contexto.")
                if update.callback_query:
                    await update.callback_query.answer("Ocurrió un error interno.", show_alert=True)
                return

            # --- CORRECCIÓN CLAVE: Añadido 'await' ---
            is_admin = await database.is_user_admin_for_bot(user_id, bot_id)
            if is_admin:
                return await func(update, context, *args, **kwargs)

            # --- CORRECCIÓN CLAVE: Añadido 'await' ---
            last_timestamp = await database.get_last_action_timestamp(user_id, bot_id, action_key)
            current_time = int(time.time())
            cooldown = ACTION_COOLDOWNS.get(action_key, 300)

            if last_timestamp and (current_time - last_timestamp) < cooldown:
                message = ""
                keyboard = []
                query = update.callback_query

                if action_key == 'start_endo_test':
                    message = "⏱️ Ya has realizado este test recientemente. Por favor, espera antes de volver a intentarlo."
                    keyboard.append([InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data='main_menu')])

                elif action_key == 'agendar_cita':
                    message = "⏱️ Ya tienes una cita agendada o has agendado una recientemente."
                    keyboard.append([InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data='main_menu')])

                if message and query:
                    await query.answer()
                    await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard))

                return

            # --- CORRECCIÓN CLAVE: Añadido 'await' ---
            await database.log_user_action(user_id, bot_id, action_key, current_time)
            return await func(update, context, *args, **kwargs)
        return wrapped
    return decorator