# features/preconsulta/patient_flow/flow_actions/checklist.py

import logging

from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from features.preconsulta.components import keyboards
from common import texts
from features.preconsulta.states import AWAITING_GENERIC_INPUT
#from features.preconsulta.patient_flow.flow_actions import loop
from ..states import AWAITING_EXAM_INPUT

logger = logging.getLogger(__name__)

def get_mock_keyboard(node_id, options_keys, selected=None):
    selected = selected or set()
    keyboard = []
    # Aquí deberías tener una lógica que cargue las opciones desde alguna parte
    # Por ahora, usamos un ejemplo:
    options = {
        "simetria_mama": ["Simétrica", "Asimétrica"],
        "radiales_mama": [str(i) for i in range(1, 13)],
        "paredes_vaginales": ["Tumores", "Condilomas", "Coloración Rosada", "Coloración Pálida"],
        "cuello_uterino": ["Sano", "Anormal", "Eritematoso", "Friable"],
        "secrecion_vaginal": ["Blanca", "Amarilla", "Gris Homogénea", "Con Sangrado"],
        "anexos_options": [
            "No se palpan, no dolorosos",
            "Anexo derecho doloroso",
            "Anexo izquierdo doloroso",
            "Se palpa masa anexial derecha",
            "Se palpa masa anexial izquierda"
        ]
    }

    current_options = options.get(options_keys, [])
    for option in current_options:
        text = f"✅ {option}" if option in selected else option
        keyboard.append([InlineKeyboardButton(text, callback_data=f"{node_id}_{option}")])

    keyboard.append([InlineKeyboardButton("➡️ Hecho", callback_data=f"{node_id}_done")])
    return InlineKeyboardMarkup(keyboard)


async def render(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict, message_id: int = None):
    text_content = texts.get_text(node['text_key'], "Selecciona las opciones:")

    node_id = context.user_data['current_node_id']
    save_key = f"{node['save_to']}_selected"
    selected_items = context.user_data.get(save_key, set())

    # Asumimos que 'keyboard_type' en el JSON corresponde a las claves del mock
    reply_markup = get_mock_keyboard(node_id, node.get('keyboard_type'), selected=selected_items)

    target_message_id = message_id or context.user_data.get('consultation_anchor_message_id')
    if not target_message_id:
        logger.error("No se encontró 'consultation_anchor_message_id' para editar en checklist.")
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
            logger.error(f"Error al editar mensaje en exam_checklist: {e}")

    return AWAITING_EXAM_INPUT


async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    query = update.callback_query
    await query.answer()

    node_id = context.user_data['current_node_id']
    selection = query.data.replace(f"{node_id}_", "")

    save_key = f"{node['save_to']}_selected"
    selected_items = context.user_data.setdefault(save_key, set())

    if selection == 'done':
        # Guardamos el resultado final como un string separado por comas
        context.user_data[node['save_to']] = ", ".join(sorted(list(selected_items))) if selected_items else "No seleccionado"
        context.user_data.pop(save_key, None) # Limpiamos la selección temporal
        return node.get('next_node')
    else:
        # Lógica de selección/deselección
        if selection in selected_items:
            selected_items.remove(selection)
        else:
            selected_items.add(selection)

        # Refrescamos el teclado para mostrar la selección actual
        new_keyboard = get_mock_keyboard(node_id, node.get('keyboard_type'), selected=selected_items)
        try:
            await query.edit_message_reply_markup(reply_markup=new_keyboard)
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                logger.warning(f"Error al refrescar teclado en exam_checklist: {e}")

        return None # Nos quedamos en el mismo nodo