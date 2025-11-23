# features/preconsulta/patient_flow/flow_actions/number_grid.py

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from common import texts
from features.preconsulta.components import keyboards
from features.preconsulta.states import AWAITING_GENERIC_INPUT


async def render(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Muestra la cuadrícula de números."""
    text_content = ""
    # --- INICIO DE LA CORRECCIÓN ---
    if 'section_header_key' in node:
        text_content += texts.get_text(node['section_header_key'], "") + "\n\n"
    text_content += texts.get_text(node['text_key'])
    #text_content = texts.get_text(node['text_key'])
    node_id = context.user_data['current_node_id']

    start = node.get('start', 1)
    end = node.get('end', 10)
    cols = node.get('cols', 5)

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=text_content,
        reply_markup=keyboards.get_number_grid_keyboard(node_id, start, end, cols),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_GENERIC_INPUT

async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Procesa la selección de un número."""
    query = update.callback_query
    await query.answer()

    node_id = context.user_data['current_node_id']
    action, value = query.data.replace(f"{node_id}_", "").split('_', 1)

    if action == "select":
        context.user_data[node['save_to']] = value
        return node.get('next_node')

    return None # Si se pulsa algo inesperado