# features/preconsulta/patient_flow/flow_actions/sexarche_picker.py
from telegram import Update
from telegram.ext import ContextTypes
# ... (todas las importaciones de year_picker.py)
from common import texts
from features.preconsulta.components import keyboards
from features.preconsulta.states import AWAITING_GENERIC_INPUT

async def render(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict, start_age: int = 9):
    """Muestra el selector de edad de sexarquia."""
    text_content = texts.get_text(node['text_key'])
    node_id = context.user_data['current_node_id']

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=text_content,
        reply_markup=keyboards.get_sexarche_grid_keyboard(node_id, start_age),
        parse_mode="HTML"
    )
    return AWAITING_GENERIC_INPUT

async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Procesa la selección de edad o la navegación."""
    query = update.callback_query
    await query.answer()

    node_id = context.user_data['current_node_id']
    action, value = query.data.replace(f"{node_id}_", "").split('_', 1)

    if action == "select":
        context.user_data[node['save_to']] = value
        return node.get('next_node')

    if action == "nav":
        new_start_age = int(value)
        # Evitamos ir a edades negativas
        if new_start_age < 1: new_start_age = 1
        await render(update, context, node, start_age=new_start_age)
        return None