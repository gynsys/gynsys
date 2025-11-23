# features/preconsulta/patient_flow/flow_actions/buttons.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from common import texts
from features.preconsulta.states import AWAITING_GENERIC_INPUT

# Intentamos importar get_ordinal. Si no existe, usamos una función simple como fallback.
try:
    from ..gyn_history_handlers import get_ordinal
except (ImportError, ModuleNotFoundError):
    def get_ordinal(n):
        """Función de fallback si la original no se encuentra."""
        return str(n)

logger = logging.getLogger(__name__)

async def render(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict, message_id: int = None):
    """Muestra una pregunta con botones, manejando plantillas de bucle y sub-bucle."""
    text_content = ""
    if 'section_header_key' in node:
        text_content += texts.get_text(node['section_header_key'], "") + "\n\n"

    if 'text_template' in node:
        template_vars = {}
        if 'loop_variable' in context.user_data:
            loop_info = context.user_data.get('loop_variable', {})
            main_loop_index = loop_info.get('index', 0)

            # Variables del bucle principal
            template_vars['index'] = main_loop_index
            template_vars['index_plus_one'] = main_loop_index + 1
            template_vars['total'] = loop_info.get('total', 0)
            template_vars['ordinal'] = get_ordinal(main_loop_index + 1)

            # --- LÓGICA DE SUB-BUCLE AÑADIDA ---
            if 'sub_loop' in loop_info:
                sub_loop = loop_info['sub_loop']
                sub_loop_index = sub_loop.get('index', 0)
                template_vars['sub_loop_index'] = sub_loop_index
                template_vars['sub_loop_index_plus_one'] = sub_loop_index + 1
                template_vars['sub_loop_ordinal'] = get_ordinal(sub_loop_index + 1)
                template_vars['sub_loop_total'] = sub_loop.get('total', 0)
            # --- FIN DE LÓGICA DE SUB-BUCLE ---

        try:
            text_content += node['text_template'].format(**template_vars)
        except KeyError as e:
            logger.error(f"Falta la clave de plantilla '{e}' en el nodo '{context.user_data.get('current_node_id')}'")
            text_content += "Error: Pregunta mal configurada."

    elif 'text_key' in node:
        text_content += texts.get_text(node['text_key'], "Por favor, selecciona una opción:")
    else:
        text_content += "Error: Pregunta no definida en el nodo."

    node_id = context.user_data['current_node_id']
    keyboard = []
    if 'options' in node:
        for i, option in enumerate(node['options']):
            keyboard.append([InlineKeyboardButton(option['label'], callback_data=f"{node_id}_{i}")])
    
    target_message_id = message_id or context.user_data.get('anchor_message_id') or context.user_data.get('consultation_anchor_message_id')
    
    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=target_message_id,
            text=text_content,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )
    except BadRequest as e:
        # Si el mensaje no existe, enviar uno nuevo
        if "message to edit not found" in str(e).lower() or "message can't be edited" in str(e).lower():
            new_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text_content,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
            # Actualizar el anchor_message_id
            context.user_data['anchor_message_id'] = new_message.message_id
        else:
            raise
    
    return AWAITING_GENERIC_INPUT

async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Procesa una selección de botón y devuelve el ID del siguiente nodo."""
    query = update.callback_query
    node_id = context.user_data['current_node_id']

    try:
        option_index = int(query.data.split('_')[-1])
        selected_option = node['options'][option_index]
    except (ValueError, IndexError):
        logger.error(f"Error al procesar callback_data '{query.data}' para el nodo de botones '{node_id}'")
        return None # No cambia de nodo

    value_to_save = selected_option.get('value', selected_option['label'])

    if 'save_to' in node:
        if 'loop_variable' in context.user_data:
            loop_info = context.user_data['loop_variable']
            # Aseguramos que el diccionario para el índice actual exista
            if len(context.user_data[loop_info['name']]) > loop_info['index']:
                 context.user_data[loop_info['name']][loop_info['index']][node['save_to']] = value_to_save
            else:
                logger.error(f"Índice de bucle fuera de rango al intentar guardar en '{node['save_to']}'")
        else:
            context.user_data[node['save_to']] = value_to_save

    return selected_option.get('next_node')