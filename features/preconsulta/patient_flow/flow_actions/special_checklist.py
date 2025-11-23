# features/preconsulta/patient_flow/flow_actions/special_checklist.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from common import texts
from features.preconsulta.components import keyboards
from features.preconsulta.states import AWAITING_GENERIC_INPUT

logger = logging.getLogger(__name__)

# Copiamos la lógica de render de checklist.py y la adaptamos
async def render(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """
    Renderizador ESPECIAL para checklists que usa la estrategia de BORRAR Y REENVIAR.
    """
    text_content = texts.get_text(node['text_key'], "Selecciona las opciones:")
    
    save_key = f"{node['save_to']}_selected"
    selected_items = context.user_data.get(save_key, set())
    
    node_id = context.user_data['current_node_id']
    keyboard_type = node.get('keyboard_type')
    
    keyboard_generators = {'substances': keyboards.get_substances_keyboard} # Solo conoce los teclados especiales
    
    reply_markup = None
    if keyboard_type in keyboard_generators:
        reply_markup = keyboard_generators[keyboard_type](node_id, selected=selected_items)

    try:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=context.user_data['anchor_message_id']
        )
    except Exception:
        pass

    message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text_content,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    
    context.user_data['anchor_message_id'] = message.message_id
    return AWAITING_GENERIC_INPUT

# Copiamos la lógica de process de checklist.py, ya que es la misma
async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Procesador ESPECIAL para checklists."""
    query = update.callback_query
    await query.answer()
    node_id = context.user_data['current_node_id']
    selection = query.data.replace(f"{node_id}_", "")
    
    save_key = f"{node['save_to']}_selected"
    selected_items = context.user_data.setdefault(save_key, set())

    options_maps = {
        'substances': {
            "alcohol": "Alcohol", "cannabis": "Marihuana/cannabis", "cocaine": "Cocaína",
            "amphetamines": "Anfetaminas", "opioids": "Opioides",
            "benzos": "Benzodiacepinas", "hallucinogens": "Alucinógenos",
            "other": "Otras sustancias"
        }
    }

    if selection == 'done':
        if not selected_items:
            final_text = "Sí, no especificado"
        else:
            current_map = options_maps.get(node.get('keyboard_type'), {})
            final_text = ", ".join(sorted([current_map.get(key, key) for key in selected_items]))
        
        # Combinamos la respuesta anterior ("Sí, actualmente") con la lista
        previous_answer = context.user_data.get(node['save_to'], "Sí")
        context.user_data[node['save_to']] = f"{previous_answer}: {final_text}"
        
        context.user_data.pop(save_key, None)
        return node.get('next_node')
    
    if selection in selected_items:
        selected_items.remove(selection)
    else:
        selected_items.add(selection)
    
    keyboard_type = node.get('keyboard_type')
    keyboard_generators = {'substances': keyboards.get_substances_keyboard}
    
    if keyboard_type in keyboard_generators:
        new_keyboard = keyboard_generators[keyboard_type](node_id, selected=selected_items)
        try:
            await query.edit_message_reply_markup(reply_markup=new_keyboard)
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                logger.warning(f"Error al refrescar special_checklist: {e}")
    
    return None