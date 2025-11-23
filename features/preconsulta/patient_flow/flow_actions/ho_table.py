# features/preconsulta/patient_flow/flow_actions/ho_table.py

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
    """Muestra la tabla del historial obstétrico."""
    text_content = texts.get_text(node['text_key'])
    node_id = context.user_data['current_node_id']

    # Recupera las selecciones actuales o empieza con un diccionario vacío
    selections = context.user_data.get('ho_table_selections', {})

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=text_content,
        reply_markup=keyboards.get_ho_table_keyboard(node_id, selections=selections),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_GENERIC_INPUT

async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Procesa una selección en la tabla del HO."""
    query = update.callback_query
    await query.answer()

    node_id = context.user_data['current_node_id']
    selection_data = query.data.replace(f"{node_id}_", "")

    selections = context.user_data.setdefault('ho_table_selections', {})

    if selection_data == 'done':
        # Guardamos el resultado final en user_data
        context.user_data[node['save_to']] = selections.copy()

        # Limpiamos la variable temporal
        context.user_data.pop('ho_table_selections', None)
        return node.get('next_node')

    if selection_data == 'ignore':
        return None

    try:
        category, value_str = selection_data.rsplit('_', 1)
        value = int(value_str)

        # Si el valor ya está seleccionado para esa categoría, lo deseleccionamos
        if selections.get(category) == value:
            del selections[category]
        else: # Si no, lo seleccionamos
            selections[category] = value

    except (ValueError, IndexError):
        logger.warning(f"Callback de ho_table con formato incorrecto: {selection_data}")
        return None

    # Redibujamos el teclado con la nueva selección
    new_keyboard = keyboards.get_ho_table_keyboard(node_id, selections=selections)
    try:
        await query.edit_message_reply_markup(reply_markup=new_keyboard)
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.warning(f"Error al refrescar ho_table: {e}")

    return None # Nos quedamos en el mismo nodo