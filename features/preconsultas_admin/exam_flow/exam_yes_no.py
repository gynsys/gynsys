# features/preconsulta/patient_flow/flow_actions/yes_no.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest
from common import texts
from ..states import AWAITING_EXAM_INPUT



from features.preconsulta.states import AWAITING_GENERIC_INPUT

logger = logging.getLogger(__name__)

def get_yes_no_keyboard(node_id: str, allow_omit: bool):
    """Genera un teclado de Sí/No, con opción de omitir."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Sí", callback_data=f"{node_id}_yes"),
            InlineKeyboardButton("🚫 No", callback_data=f"{node_id}_no")
        ]
    ]
    if allow_omit:
        keyboard.append([InlineKeyboardButton("➡️ Omitir Ítem", callback_data=f"{node_id}_omit")])

    return InlineKeyboardMarkup(keyboard)


async def render(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict, message_id: int = None):
    text_content = texts.get_text(node['text_key'], "Por favor, responde:")

    node_id = context.user_data['current_node_id']
    allow_omit = node.get('allow_omit', False)
    reply_markup = get_yes_no_keyboard(node_id, allow_omit)

    target_message_id = message_id or context.user_data.get('consultation_anchor_message_id')
    if not target_message_id:
        logger.error("No se encontró 'consultation_anchor_message_id' para editar en yes_no.")
        return ConversationHandler.END

    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=target_message_id,
            text=text_content,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error al editar mensaje en exam_yes_no: {e}")

    return AWAITING_EXAM_INPUT


async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    query = update.callback_query
    await query.answer()

    node_id = context.user_data['current_node_id']
    selection = query.data.replace(f"{node_id}_", "")

    if selection == "omit":
        # Usamos next_on_omit o el next_node general
        return node.get('next_on_omit', node.get('next_node'))

    if selection == "yes":
        context.user_data[node['save_to']] = "Sí"
        # --- CORRECCIÓN: Usar next_on_yes ---
        return node.get('next_on_yes')

    if selection == "no":
        context.user_data[node['save_to']] = "No"
        # --- CORRECCIÓN: Usar next_on_no ---
        return node.get('next_on_no')

    return None