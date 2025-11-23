#numeric_keypad.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from common import texts
from features.preconsulta.components import keyboards
from features.preconsulta.states import AWAITING_GENERIC_INPUT

logger = logging.getLogger(__name__)

async def render(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Muestra la pregunta y el teclado numérico por primera vez."""
    context.user_data['numeric_keypad_input'] = "" # Limpiamos/inicializamos

    question_text = texts.get_text(node['text_key'])
    node_id = context.user_data['current_node_id']

    # La primera vez, sí usamos edit_message_text para poner la pregunta
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=question_text,
        reply_markup=keyboards.get_numeric_keypad_keyboard(node_id), # Muestra "___"
        parse_mode=ParseMode.HTML
    )
    return AWAITING_GENERIC_INPUT

async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Procesa un clic en el teclado numérico usando actualizaciones rápidas."""
    query = update.callback_query
    await query.answer()

    node_id = context.user_data['current_node_id']
    action_type, value = query.data.replace(f"{node_id}_", "").split('_', 1)

    current_input = context.user_data.get('numeric_keypad_input', "")

    should_refresh_keyboard = False

    if action_type == "digit":
        current_input += value
        should_refresh_keyboard = True

    elif action_type == "action":
        if value == "backspace":
            current_input = current_input[:-1]
            should_refresh_keyboard = True

        elif value == "clear":
            current_input = ""
            should_refresh_keyboard = True

        elif value == "submit":
            context.user_data[node['save_to']] = current_input
            context.user_data.pop('numeric_keypad_input', None)
            return node.get('next_node')

    context.user_data['numeric_keypad_input'] = current_input

    if should_refresh_keyboard:
        try:
            # --- ¡LA MAGIA DE LA VELOCIDAD! ---
            # Solo actualizamos el teclado, no el texto. Es casi instantáneo.
            await query.edit_message_reply_markup(
                reply_markup=keyboards.get_numeric_keypad_keyboard(node_id, display_value=current_input)
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                logger.warning(f"Error al refrescar numeric_keypad: {e}")

    return None