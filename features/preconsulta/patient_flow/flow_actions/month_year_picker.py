# features/preconsulta/patient_flow/flow_actions/month_year_picker.py
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from common import texts
from features.preconsulta.components import keyboards
from features.preconsulta.states import AWAITING_GENERIC_INPUT

logger = logging.getLogger(__name__)

async def render(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict, year: int = None):
    """Muestra el selector de Mes/Año."""
    if year is None:
        year = datetime.now().year
    
    text_content = texts.get_text(node['text_key'], "Selecciona mes y año:")
    node_id = context.user_data['current_node_id']
    allow_text = node.get('allow_text')

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=text_content,
        reply_markup=keyboards.get_month_year_picker_keyboard(node_id, year, allow_text),
        parse_mode="HTML"
    )
    return AWAITING_GENERIC_INPUT

async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Procesa la selección de mes/año, la navegación o el botón 'Nunca'."""
    query = update.callback_query
    await query.answer()

    node_id = context.user_data['current_node_id']
    selection = query.data.replace(f"{node_id}_", "")
    
    # Caso 1: Se seleccionó un mes
    if selection.startswith("select_"):
        year_month = selection.split('_', 1)[1]
        context.user_data[node['save_to']] = year_month
        return node.get('next_node')

    # Caso 2: Se usó la navegación de año
    if selection.startswith("nav_"):
        try:
            new_year = int(selection.split('_', 1)[1])
            # Volvemos a renderizar el teclado con el nuevo año
            await render(update, context, node, year=new_year)
        except (ValueError, IndexError):
            logger.warning(f"Navegación de calendario inválida: {selection}")
        return None # Nos quedamos en el mismo nodo

    # Caso 3: Se presionó el botón 'allow_text' (ej. "Nunca")
    allow_text = node.get('allow_text', '').lower()
    if allow_text and selection == allow_text:
        context.user_data[node['save_to']] = node['allow_text'] # Guardamos el texto literal
        return node.get('next_node')
        
    return None