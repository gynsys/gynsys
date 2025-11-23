# features/preconsulta/editing/handlers.py
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from common import texts
from features.preconsulta.states import EDITING_FIELD  # Cambiado a absoluto

# Cambia estos imports:
from features.preconsulta.patient_flow.personal_info_handlers import show_personal_info_summary
from features.preconsulta.patient_flow.general_medical_handlers import show_medical_history_summary
logger = logging.getLogger(__name__)



# features/preconsulta/editing/handlers.py

async def prompt_to_edit_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        # El formato esperado es: edit_{prefix}_{field_key}:{question_key}
        if ':' not in query.data:
            logger.error(f"Formato de callback_data incorrecto: {query.data}")
            await query.edit_message_text("❌ Error: Formato de edición inválido.")
            return ConversationHandler.END

        main_part, question_key = query.data.split(':', 1)
        _, section_prefix, field_key = main_part.split('_', 2)

    except (ValueError, IndexError) as e:
        logger.error(f"Error: callback_data de edición mal formado: {query.data}. Error: {e}")
        await query.edit_message_text("❌ Error: Callback de edición inválido.")
        return ConversationHandler.END

    context.user_data['editing_info'] = {
        'section': section_prefix,
        'key': field_key
    }

    prompt_key = f'preconsulta.{question_key}'
    prompt_text = texts.get_text(prompt_key, f"Por favor, introduce el nuevo valor para {field_key.replace('_', ' ').title()}:")

    await query.edit_message_text(text=prompt_text)

    return EDITING_FIELD

async def receive_edited_field(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe el nuevo valor, lo guarda y vuelve a la función de resumen apropiada."""
    editing_info = context.user_data.get('editing_info')
    if not editing_info:
        await update.message.reply_text("Tu sesión de edición ha expirado. Por favor, reinicia.")
        return -1 # ConversationHandler.END

    field_key = editing_info['key']
    section_prefix = editing_info['section']

    # Guardamos el nuevo valor
    context.user_data[field_key] = update.message.text
    await update.message.delete()

    if field_key == 'family_history_mother':
        context.user_data.pop('mother_history_selected', None)
    elif field_key == 'family_history_father':
        context.user_data.pop('father_history_selected', None)
    elif field_key == 'personal_history':
        context.user_data.pop('personal_history_selected', None)
    # Limpiamos los datos de edición para el próximo ciclo

    context.user_data.pop('editing_info', None)

    # --- Mapeo para saber a qué función de resumen volver ---
    # Importaciones locales para evitar importaciones circulares a nivel de módulo

    # from ..family_history_handlers import show_family_summary # Ejemplo futuro

    summary_callers = {
        'pi': show_personal_info_summary,
        'mh': show_medical_history_summary, # <-- AÑADIR ESTA LÍNEA
    }
    # Llamamos a la función de resumen correcta basándonos en el prefijo de la sección
    if section_prefix in summary_callers:
        return await summary_callers[section_prefix](update, context)
    else:
        logger.error(f"No se encontró una función de resumen para el prefijo: {section_prefix}")
        return -1