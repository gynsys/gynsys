# En exam_buttons.py
import logging
from telegram.error import BadRequest
from telegram.ext import (
    ConversationHandler
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from common import texts

from ..states import AWAITING_EXAM_INPUT
logger = logging.getLogger(__name__)

async def render(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict, message_id: int = None):
    """Renderizador de botones específico para el flujo del examen del admin."""
    text_content = texts.get_text(node['text_key'], "Selecciona una opción:")

    # --- INICIO DE LA CORRECCIÓN ---
    # Usamos SIEMPRE el current_node_id que el motor tiene guardado.
    node_id = context.user_data.get('current_node_id')
    # --- FIN DE LA CORRECCIÓN ---

    keyboard = []
    options = node.get('options', [])
    for i, option in enumerate(options):
        # El callback_data ahora se construye con el ID de nodo correcto
        keyboard.append([InlineKeyboardButton(option['label'], callback_data=f"{node_id}_{i}")])

    if node.get('allow_omit'):
        keyboard.append([InlineKeyboardButton("➡️ Omitir Ítem", callback_data=f"{node_id}_omit")])

    target_message_id = message_id or context.user_data.get('consultation_anchor_message_id')
    if not target_message_id:
        logger.error("No se encontró 'consultation_anchor_message_id' para editar.")
        return ConversationHandler.END

    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=target_message_id,
            text=text_content,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error al editar mensaje en exam_buttons: {e}")

    return AWAITING_EXAM_INPUT



async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """
    Procesa una selección de botón, guarda el dato y devuelve el siguiente nodo.
    """
    query = update.callback_query

    # Es importante responder al query al principio
    await query.answer()

    node_id = context.user_data.get('current_node_id')
    selection = query.data.replace(f"{node_id}_", "")

    if selection == 'omit':
        return node.get('next_on_omit')

    try:
        option_index = int(selection)
        selected_option = node['options'][option_index]
    except (ValueError, IndexError):
        logger.error(f"Error al procesar callback_data '{query.data}' para el nodo '{node_id}'")
        return None # No hacer nada si el callback es inválido

    value_to_save = selected_option.get('value', selected_option['label'])
    if 'save_to' in node:
        context.user_data[node['save_to']] = value_to_save

    # --- INICIO DE LA CORRECCIÓN CLAVE ---
    # 1. Intenta obtener el next_node de la opción específica (si existe).
    # 2. Si no existe, usa el next_node general del nodo.
    return selected_option.get('next_node', node.get('next_node'))
    # --- FIN DE LA CORRECCIÓN CLAVE ---