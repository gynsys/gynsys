# features/preconsulta/patient_flow/flow_actions/yes_no.py

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from features.preconsulta.components import keyboards
from common import texts
from features.preconsulta.states import AWAITING_GENERIC_INPUT

async def render(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict, message_id: int = None):
    """Muestra una pregunta con teclado Sí/No."""
    from telegram.error import BadRequest
    
    text_content = ""
    if 'section_header_key' in node:
        text_content += texts.get_text(node['section_header_key'], "") + "\n\n"
    text_content += texts.get_text(node['text_key'], "Por favor, selecciona una opción:")
    target_message_id = message_id or context.user_data.get('anchor_message_id') or context.user_data.get('consultation_anchor_message_id')
    
    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=target_message_id,
            text=text_content,
            reply_markup=keyboards.get_yes_no_keyboard(context.user_data['current_node_id']),
            parse_mode=ParseMode.HTML
        )
    except BadRequest as e:
        # Si el mensaje no existe, enviar uno nuevo
        if "message to edit not found" in str(e).lower() or "message can't be edited" in str(e).lower():
            new_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text_content,
                reply_markup=keyboards.get_yes_no_keyboard(context.user_data['current_node_id']),
                parse_mode=ParseMode.HTML
            )
            # Actualizar el anchor_message_id
            context.user_data['anchor_message_id'] = new_message.message_id
        else:
            raise
    
    return AWAITING_GENERIC_INPUT

async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Procesa una respuesta de Sí/No y devuelve el ID del siguiente nodo."""
    query = update.callback_query

    if query.data.endswith('_yes'):
        # Guardamos el valor "Sí" si está definido en el JSON, si no, "Sí" por defecto
        context.user_data[node['save_to']] = node.get('value_on_yes', 'Sí')
        # Usamos el 'next_on_yes' si existe, si no, el 'next_node' genérico
        return node.get('next_on_yes', node.get('next_node'))
    else: # 'no'
        # Guardamos el valor "No"
        context.user_data[node['save_to']] = node.get('value_on_no', 'No')
        # Usamos el 'next_on_no' si existe, si no, el 'next_node' genérico
        return node.get('next_on_no', node.get('next_node'))