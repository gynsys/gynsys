# features/preconsulta/patient_flow/generic_flow_handlers.py

import json
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

from common import texts
from features.preconsulta.states import *
from features.preconsulta.components import keyboards

# --- Importamos las funciones de "salida" de nuestros módulos ---
from .personal_info_handlers import show_personal_info_summary
from .gyn_history_handlers import ask_gyn_history_start

logger = logging.getLogger(__name__)

# --- Cargar el Flujo ---
try:
    with open('features/preconsulta/flows/personal_info_flow.json', 'r', encoding='utf-8') as f:
        preconsultation_flow = json.load(f)
except FileNotFoundError:
    logger.error("¡CRÍTICO! No se encontró el archivo de flujo 'personal_info_flow.json'")
    preconsultation_flow = None


# --- El Motor de Flujos ---

async def render_node(update: Update, context: ContextTypes.DEFAULT_TYPE, node_id: str):
    """Muestra el paso (nodo) actual al usuario."""
    chat_id = update.effective_chat.id
    flow = context.user_data.get('flow')
    if not flow or node_id not in flow['nodes']:
        await context.bot.send_message(chat_id, "Error: Flujo de conversación no encontrado.")
        return ConversationHandler.END

    node = flow['nodes'][node_id]
    context.user_data['current_node_id'] = node_id

    node_type = node['type']

    # --- LÓGICA DE DESPACHO CORREGIDA ---
    # Primero, verificamos si es un nodo de acción, ya que estos no muestran texto.
    if node_type == 'action':
        action_handlers = {
            "show_personal_info_summary": show_personal_info_summary
        }
        handler_name = node.get('handler')
        if handler_name in action_handlers:
            # Llamamos a la función de acción (ej. la que muestra el resumen)
            # Esta función se encargará de devolver el siguiente estado correcto.
            return await action_handlers[handler_name](update, context)
        else:
            logger.error(f"Acción desconocida en el flujo: {handler_name}")
            return ConversationHandler.END

    # Si no es una acción, entonces es un nodo que muestra algo al usuario.
    text_content = ""
    if 'section_header_key' in node:
        text_content += texts.get_text(node['section_header_key'], "") + "\n\n"

    # Esta línea ahora está protegida, solo se ejecuta para nodos que no son de tipo 'action'.
    text_content += texts.get_text(node['text_key'], "Por favor, selecciona una opción:")

    reply_markup = None
    next_state = ConversationHandler.END

    if node_type == 'text_input':
        next_state = AWAITING_GENERIC_INPUT

    elif node_type == 'yes_no':
        reply_markup = keyboards.get_yes_no_keyboard(node_id)
        next_state = AWAITING_GENERIC_INPUT

    elif node_type == 'checklist':
        save_key = f"{node['save_to']}_selected"
        selected_items = context.user_data.get(save_key, set())
        keyboard_type = node.get('keyboard_type')
        if keyboard_type == 'pathologies':
            reply_markup = keyboards.get_pathologies_keyboard(node_id, selected=selected_items)
        next_state = AWAITING_GENERIC_INPUT

    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=context.user_data['anchor_message_id'],
        text=text_content,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    return next_state


async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa la entrada del usuario, la valida y decide el siguiente paso."""
    flow = context.user_data.get('flow')
    node_id = context.user_data.get('current_node_id')
    node = flow['nodes'][node_id]

    next_node_id = None

    if update.message and update.message.text:
        user_input = update.message.text
        await update.message.delete()

        ### CORRECCIÓN ###: Toda esta lógica debe estar DENTRO del 'if update.message...'

        # --- Validación ---
        validation_config = node.get('validation')
        if validation_config:
            error_key = f"{node['save_to']}_error_attempts"
            is_valid = True

            if validation_config['type'] == 'numeric':
                user_input_numeric = user_input.replace(',', '.')
                try:
                    float(user_input_numeric)
                except ValueError:
                    is_valid = False

            if not is_valid:
                # La validación falló, mostramos el mensaje de error progresivo
                attempts = context.user_data.get(error_key, 0) + 1
                context.user_data[error_key] = attempts

                if attempts > 3:
                    await context.bot.send_message(update.effective_chat.id, "Demasiados intentos incorrectos. La preconsulta ha sido cancelada.")
                    context.user_data.clear()
                    return ConversationHandler.END

                error_messages = validation_config.get('error_messages', ["Formato incorrecto."])
                error_text = error_messages[min(attempts - 1, len(error_messages) - 1)]

                error_msg_id = context.user_data.get('temp_error_message_id')
                if error_msg_id:
                    try:
                        await context.bot.edit_message_text(update.effective_chat.id, error_msg_id, error_text, parse_mode=ParseMode.HTML)
                    except BadRequest:
                        msg = await context.bot.send_message(update.effective_chat.id, error_text, parse_mode=ParseMode.HTML)
                        context.user_data['temp_error_message_id'] = msg.message_id
                else:
                    msg = await context.bot.send_message(update.effective_chat.id, error_text, parse_mode=ParseMode.HTML)
                    context.user_data['temp_error_message_id'] = msg.message_id

                return AWAITING_GENERIC_INPUT # Nos quedamos esperando una nueva entrada

        # Si la validación pasa (o no había validación)
        if 'temp_error_message_id' in context.user_data:
            try:
                await context.bot.delete_message(update.effective_chat.id, context.user_data.pop('temp_error_message_id'))
            except BadRequest:
                pass
        context.user_data.pop(f"{node['save_to']}_error_attempts", None)

        # --- Guardado de datos ---
        ### CORRECCIÓN ###: Eliminada la indentación extra
        context.user_data[node['save_to']] = user_input
        next_node_id = node.get('next_node')

    elif update.callback_query:
        query = update.callback_query
        await query.answer()

        node_type = node.get('type')
        if node_type == 'yes_no':
            if query.data.endswith('_yes'):
                next_node_id = node.get('next_on_yes')
            else:
                context.user_data[node['save_to']] = node.get('value_on_no', 'No')
                next_node_id = node.get('next_on_no')

        elif node_type == 'checklist':
            selection = query.data.replace(f"{node_id}_", "")
            save_key = f"{node['save_to']}_selected"
            selected_items = context.user_data.setdefault(save_key, set())

            if selection == 'done':
                if not selected_items:
                    final_text = "Sí, no especificado"
                else:
                    # Usamos los textos de los botones para el resumen final
                    final_text = ", ".join(sorted(list(selected_items)))
                context.user_data[node['save_to']] = final_text
                context.user_data.pop(save_key, None)
                next_node_id = node.get('next_node')

            elif selection == 'other':
                # Por ahora no implementamos 'other', lo tratamos como una opción más.
                # Puedes añadir la lógica para pedir texto aquí
                pass

            else: # Es una selección normal de la lista
                if selection in selected_items:
                    selected_items.remove(selection)
                else:
                    selected_items.add(selection)

                keyboard_type = node.get('keyboard_type')
                new_keyboard = None
                if keyboard_type == 'pathologies':
                    new_keyboard = keyboards.get_pathologies_keyboard(node_id, selected=selected_items)

                if new_keyboard:
                    try:
                        await query.edit_message_reply_markup(reply_markup=new_keyboard)
                    except BadRequest as e:
                        if "Message is not modified" not in str(e):
                            logger.warning(f"Error al refrescar checklist: {e}")

                return AWAITING_GENERIC_INPUT

    # --- TRANSICIÓN ---
    if next_node_id == "END_OF_MODULE":
        return await ask_gyn_history_start(update, context)
    elif next_node_id:
        return await render_node(update, context, next_node_id)
    else:
        logger.warning(f"No se encontró 'next_node' para el nodo {node_id} o la acción. La conversación podría detenerse aquí.")
        # Si es un callback y no hay next_node, nos quedamos esperando.
        if update.callback_query:
            return AWAITING_GENERIC_INPUT
        return ConversationHandler.END


async def start_personal_info_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Función de entrada que prepara e inicia el motor de flujos."""
    if not preconsultation_flow:
        if update.callback_query: await update.callback_query.answer()
        await context.bot.send_message(update.effective_chat.id, "Error crítico: No se pudo cargar el flujo de la preconsulta.")
        return ConversationHandler.END

    context.user_data.clear()
    context.user_data['flow'] = preconsultation_flow
    start_node_id = preconsultation_flow['start_node']

    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.message.delete()
        except BadRequest: pass

    intro_text = texts.get_text('preconsulta.start_intro')
    message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=intro_text,
        parse_mode=ParseMode.HTML
    )
    context.user_data['anchor_message_id'] = message.message_id

    return await render_node(update, context, start_node_id)