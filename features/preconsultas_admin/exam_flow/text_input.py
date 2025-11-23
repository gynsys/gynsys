# features/preconsulta/patient_flow/flow_actions/text_input.py

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest
from common import texts
from features.preconsulta.states import AWAITING_GENERIC_INPUT
from ..states import AWAITING_EXAM_INPUT
# Intentamos importar get_ordinal. Si no existe, usamos una función simple como fallback.
try:
    from ..gyn_history_handlers import get_ordinal
except (ImportError, ModuleNotFoundError):
    def get_ordinal(n):
        """Función de fallback si la original no se encuentra."""
        return str(n)

logger = logging.getLogger(__name__)



async def render(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict, message_id: int = None):
    """Renderizador de texto específico para el flujo del examen del admin."""
    text_content = texts.get_text(node['text_key'], "Por favor, introduce el dato:")

    target_message_id = message_id or context.user_data.get('consultation_anchor_message_id')
    if not target_message_id:
        logger.error("No se encontró 'consultation_anchor_message_id' para editar.")
        return ConversationHandler.END

    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=target_message_id,
            text=text_content,
            parse_mode=ParseMode.HTML,
            reply_markup=None # Los inputs de texto no llevan teclado inline
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error al editar mensaje en exam_text_input: {e}")

    return AWAITING_EXAM_INPUT




async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    user_input = update.message.text
    await update.message.delete()
    chat_id = update.effective_chat.id

    validation_config = node.get('validation')
    if validation_config:
        is_valid = False
        if validation_config['type'] == 'numeric':
            try:
                float(user_input.replace(',', '.'))
                is_valid = True
            except ValueError:
                pass

        if not is_valid:
            error_key = f"{node.get('save_to', 'unknown')}_error_attempts"
            attempts = context.user_data.get(error_key, 0) + 1
            context.user_data[error_key] = attempts

            if attempts > 3:
                await context.bot.send_message(chat_id, "Demasiados intentos incorrectos. La preconsulta ha sido cancelada.")
                context.user_data.clear()
                return ConversationHandler.END

            error_messages = validation_config.get('error_messages', ["Formato incorrecto."])
            error_text = error_messages[min(attempts - 1, len(error_messages) - 1)]

            error_msg_id = context.user_data.get('temp_error_message_id')
            if error_msg_id:
                try:
                    await context.bot.edit_message_text(chat_id, error_msg_id, error_text, parse_mode=ParseMode.HTML)
                except BadRequest:
                    msg = await context.bot.send_message(chat_id, error_text, parse_mode=ParseMode.HTML)
                    context.user_data['temp_error_message_id'] = msg.message_id
            else:
                msg = await context.bot.send_message(chat_id, error_text, parse_mode=ParseMode.HTML)
                context.user_data['temp_error_message_id'] = msg.message_id

            return None

    if 'temp_error_message_id' in context.user_data:
        try:
            await context.bot.delete_message(chat_id, context.user_data.pop('temp_error_message_id'))
        except BadRequest:
            pass
    context.user_data.pop(f"{node.get('save_to', '')}_error_attempts", None)

    if 'save_to' in node:
        context.user_data[node['save_to']] = user_input

    return node.get('next_node')