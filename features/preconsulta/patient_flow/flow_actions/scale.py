# features/preconsulta/patient_flow/flow_actions/scale.py
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from features.preconsulta.components import keyboards
from common import texts
from features.preconsulta.states import AWAITING_GENERIC_INPUT

async def render(update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Muestra un teclado de escala de dolor."""
    # CORRECCIÓN: Usar el text_key definido en el nodo del JSON
    text_content = texts.get_text(node['text_key'], "Por favor, selecciona la intensidad de tu dolor:")

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=text_content,
        reply_markup=keyboards.get_pain_scale_keyboard(context.user_data['current_node_id']),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_GENERIC_INPUT

async def process(update, context, node):
    """Procesa la selección de la escala, la guarda y devuelve el siguiente nodo."""
    query = update.callback_query
    node_id = context.user_data['current_node_id']

    # Ignoramos los botones de texto ('Leve', 'Moderado', etc.)
    if "ignore" in query.data:
        await query.answer()
        return None # No cambia de nodo

    # Extraemos el valor numérico
    scale_value = query.data.replace(f"{node_id}_", "")

    # Guardamos el valor en la clave especificada por "save_to" en el JSON
    context.user_data[node['save_to']] = scale_value

    # Devolvemos el ID del siguiente nodo para que el motor continúe
    return node.get('next_node')