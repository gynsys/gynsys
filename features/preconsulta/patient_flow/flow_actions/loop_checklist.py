# features/preconsulta/patient_flow/flow_actions/loop_checklist.py

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
    """Muestra un teclado de checklist editando el mensaje ancla."""
    text_content = ""
    if 'section_header_key' in node:
        text_content += texts.get_text(node['section_header_key'], "") + "\n\n"
    
    text_content += texts.get_text(node['text_key'], "Selecciona las opciones:")
    
    save_key = f"{node['save_to']}_selected"
    selected_items = context.user_data.get(save_key, set())
    
    node_id = context.user_data['current_node_id']
    keyboard_type = node.get('keyboard_type')
    
    keyboard_generators = {
        'birth_complications': keyboards.get_birth_complications_keyboard,
        # Puedes añadir más tipos de checklist para bucles aquí en el futuro
    }
    
    reply_markup = None
    if keyboard_type in keyboard_generators:
        reply_markup = keyboard_generators[keyboard_type](node_id, selected=selected_items)
    else:
        logger.error(f"Tipo de teclado de loop_checklist desconocido: '{keyboard_type}'")

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=text_content,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    return AWAITING_GENERIC_INPUT


async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Procesa una selección de checklist y la guarda dentro del diccionario del bucle."""
    query = update.callback_query
    await query.answer()
    node_id = context.user_data['current_node_id']
    selection = query.data.replace(f"{node_id}_", "")
    
    save_key = f"{node['save_to']}_selected"
    selected_items = context.user_data.setdefault(save_key, set())

    options_maps = {
        'birth_complications': {
            "preeclampsia": "Preclamsia",
            "placenta_previa": "Placenta Previa",
            "hemorragia": "Hemorragias",
            "none": "Sin complicaciones"
        }
    }

    if selection == 'done':
        if not selected_items:
            final_text = "No especificado"
        else:
            current_map = options_maps.get(node.get('keyboard_type'), {})
            final_text = ", ".join(sorted([current_map.get(key, key) for key in selected_items]))

        # --- LÓGICA DE GUARDADO EN BUCLE ---
        if 'loop_variable' in context.user_data:
            loop_info = context.user_data['loop_variable']
            if len(context.user_data.get(loop_info['name'], [])) > loop_info['index']:
                 context.user_data[loop_info['name']][loop_info['index']][node['save_to']] = final_text
            else:
                logger.error(f"Índice de bucle fuera de rango al intentar guardar en '{node['save_to']}'")
        else:
            logger.warning(f"Se usó loop_checklist fuera de un bucle para el nodo '{node_id}'")
        # --- FIN DE LÓGICA DE GUARDADO ---
        
        context.user_data.pop(save_key, None)
        return node.get('next_node')
    
    # Lógica para manejar la selección de "Sin complicaciones"
    if selection == 'none':
        if 'none' in selected_items:
            selected_items.clear()
        else:
            selected_items.clear()
            selected_items.add('none')
    else:
        # Si se selecciona otra opción, quitamos "Sin complicaciones"
        selected_items.discard('none')
        if selection in selected_items:
            selected_items.remove(selection)
        else:
            selected_items.add(selection)
    
    # Refrescar el teclado
    keyboard_type = node.get('keyboard_type')
    keyboard_generators = {'birth_complications': keyboards.get_birth_complications_keyboard}
    
    if keyboard_type in keyboard_generators:
        new_keyboard = keyboard_generators[keyboard_type](node_id, selected=selected_items)
        try:
            await query.edit_message_reply_markup(reply_markup=new_keyboard)
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                logger.warning(f"Error al refrescar loop_checklist: {e}")
    
    return None # Quédate en este nodo