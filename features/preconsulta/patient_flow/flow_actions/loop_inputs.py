# features/preconsulta/patient_flow/flow_actions/loop_inputs.py

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest
from . import text_input, buttons, calendar

logger = logging.getLogger(__name__)

# --- Renders ---
render_text = text_input.render
render_buttons = buttons.render
render_calendar = calendar.render

# --- Processors ---
async def process_text_in_loop(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    print("--- 5a. [LOOP_INPUTS] Entrando a process_text_in_loop ---")

    user_input = update.message.text
    await update.message.delete()
    chat_id = update.effective_chat.id

    validation_config = node.get('validation')
    if validation_config:
        is_valid = False
        if validation_config['type'] == 'numeric':
            try:
                float(user_input.replace(',', '.'))
                is_valid = True
            except ValueError:
                pass

        if not is_valid:
            print("--- 5x. [LOOP_INPUTS] Validación fallida. Devolviendo None. ---")
            error_key = f"{node['save_to']}_error_attempts_loop"
            attempts = context.user_data.get(error_key, 0) + 1
            context.user_data[error_key] = attempts

            if attempts > 3:
                await context.bot.send_message(chat_id, "Demasiados intentos incorrectos. La preconsulta ha sido cancelada.")
                context.user_data.clear()
                return ConversationHandler.END

            error_messages = validation_config.get('error_messages', ["Formato incorrecto."])
            error_text = error_messages[min(attempts - 1, len(error_messages) - 1)]

            error_msg_id = context.user_data.get('temp_error_message_id')
            if error_msg_id:
                try:
                    await context.bot.edit_message_text(chat_id, error_msg_id, error_text, parse_mode=ParseMode.HTML)
                except BadRequest:
                    msg = await context.bot.send_message(chat_id, error_text, parse_mode=ParseMode.HTML)
                    context.user_data['temp_error_message_id'] = msg.message_id
            else:
                msg = await context.bot.send_message(chat_id, error_text, parse_mode=ParseMode.HTML)
                context.user_data['temp_error_message_id'] = msg.message_id
            return None

    if 'temp_error_message_id' in context.user_data:
        try:
            await context.bot.delete_message(chat_id, context.user_data.pop('temp_error_message_id'))
        except BadRequest:
            pass
    context.user_data.pop(f"{node.get('save_to', '')}_error_attempts_loop", None)

    if 'loop_variable' in context.user_data and 'save_to' in node:
        loop_info = context.user_data['loop_variable']
        index = loop_info['index']
        save_key = node['save_to']
        print(f"--- 5b. [LOOP_INPUTS] Guardando '{user_input}' en la lista '{loop_info['name']}', índice {index}, clave '{save_key}' ---")
        context.user_data[loop_info['name']][index][save_key] = user_input
    else:
        print(f"--- 5b. [LOOP_INPUTS] WARNING: No se encontró 'loop_variable' o 'save_to' para guardar el dato ---")

    next_node_to_return = node.get('next_node')
    print(f"--- 5c. [LOOP_INPUTS] Devolviendo el siguiente nodo: '{next_node_to_return}' ---")

    return next_node_to_return

async def process_buttons_in_loop(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    query = update.callback_query
    node_id = context.user_data['current_node_id']

    try:
        option_index = int(query.data.split('_')[-1])
        selected_option = node['options'][option_index]
    except (ValueError, IndexError):
        logger.error(f"Error procesando callback en loop_buttons: {query.data}")
        return None

    value_to_save = selected_option.get('value', selected_option['label'])

    if 'save_to' in node and 'loop_variable' in context.user_data:
        loop_info = context.user_data['loop_variable']
        context.user_data[loop_info['name']][loop_info['index']][node['save_to']] = value_to_save

    return selected_option.get('next_node')

async def process_calendar_in_loop(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    query = update.callback_query
    node_id = context.user_data['current_node_id']
    selection = query.data.replace(f"{node_id}_", "")

    value_to_save = None
    next_node = None

    if "allow_text" in node and selection == node['allow_text'].lower():
        value_to_save = node['allow_text']
        next_node = node.get('next_node')
    elif selection.startswith("day_"):
        value_to_save = selection.replace("day_", "")
        next_node = node.get('next_node')

    if value_to_save and 'loop_variable' in context.user_data:
        loop_info = context.user_data['loop_variable']
        context.user_data[loop_info['name']][loop_info['index']][node['save_to']] = value_to_save
        return next_node

    await calendar.process(update, context, node)
    return None