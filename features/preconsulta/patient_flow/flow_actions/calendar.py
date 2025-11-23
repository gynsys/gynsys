# features/preconsulta/patient_flow/flow_actions/calendar.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from common import texts
from features.preconsulta.states import AWAITING_GENERIC_INPUT
from features.preconsulta.components.calendar import FUMCalendar

logger = logging.getLogger(__name__)

# --- Esta función auxiliar es nueva y crucial ---
def build_adapted_keyboard(calendar_markup: InlineKeyboardMarkup, node_id: str, node: dict):
    """Toma un teclado de calendario y adapta sus callbacks para el motor de flujos."""
    new_keyboard_rows = []
    for row in calendar_markup.inline_keyboard:
        new_row = []
        for button in row:
            new_callback = button.callback_data.replace('fum_cal_', f'{node_id}_')
            new_row.append(InlineKeyboardButton(button.text, callback_data=new_callback))
        new_keyboard_rows.append(new_row)
    
    if "allow_text" in node:
        new_keyboard_rows.append([InlineKeyboardButton(f"🚫 {node['allow_text']}", callback_data=f"{node_id}_{node['allow_text'].lower()}")])
    
    return InlineKeyboardMarkup(new_keyboard_rows)


async def render(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Muestra el teclado de calendario por primera vez (mes actual)."""
    text_content = texts.get_text(node['text_key'], "Por favor, selecciona una fecha:")
    node_id = context.user_data['current_node_id']

    # Llamamos a create_calendar sin argumentos para obtener el mes actual
    calendar_markup = FUMCalendar().create_calendar()
    
    # Usamos la función auxiliar para adaptar el teclado
    adapted_keyboard = build_adapted_keyboard(calendar_markup, node_id, node)

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=text_content,
        reply_markup=adapted_keyboard,
        parse_mode=ParseMode.HTML
    )
    return AWAITING_GENERIC_INPUT


async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Procesa una selección de calendario, incluyendo la navegación."""
    query = update.callback_query
    await query.answer()
    
    node_id = context.user_data['current_node_id']
    selection = query.data.replace(f"{node_id}_", "")

    if "allow_text" in node and selection == node['allow_text'].lower():
        context.user_data[node['save_to']] = node['allow_text']
        return node.get('next_node')

    if selection.startswith("day_"):
        selected_date_str = selection.replace("day_", "")
        context.user_data[node['save_to']] = selected_date_str
        return node.get('next_node')

    if selection.startswith("nav_"):
        try:
            year, month = map(int, selection.split('_')[-1].split('-'))
            
            # --- LA CORRECCIÓN CLAVE ESTÁ AQUÍ ---
            # 1. Creamos una instancia de tu calendario
            calendar_instance = FUMCalendar()
            # 2. Llamamos a create_calendar CON los argumentos de año y mes
            new_calendar_markup = calendar_instance.create_calendar(year=year, month=month)
            # 3. Adaptamos el nuevo teclado
            adapted_keyboard = build_adapted_keyboard(new_calendar_markup, node_id, node)

            # Editamos el mensaje actual para mostrar el nuevo teclado del calendario
            await query.edit_message_reply_markup(reply_markup=adapted_keyboard)

        except (ValueError, IndexError, AttributeError) as e:
            logger.error(f"Error al procesar navegación de calendario: {e}")
        
        return None

    return None