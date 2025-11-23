# features/preconsulta/general_medical_handlers.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from telegram.constants import ParseMode

from .gyn_history_handlers import ask_gyn_history_start
from common import texts  # Importamos el módulo de textos
from features.preconsulta.states import *
from common.helpers import escape_html
from features.preconsulta.editing.keyboards import get_med_history_summary_keyboard # Importamos el nuevo teclado

from features.preconsulta.components import keyboards  # Para teclados generales como get_yes_no_keyboard

logger = logging.getLogger(__name__)


async def ask_personal_history_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query: await update.callback_query.answer()

    question_text = texts.get_text('preconsulta.ask_personal_history')

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
        text=question_text,
        reply_markup=keyboards.get_yes_no_keyboard('personal_history_bool'),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_PERSONAL_HISTORY_BOOL

async def handle_personal_history_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data.endswith('_yes'):
        context.user_data['personal_history_selected'] = set()
        await query.edit_message_text(
            text=texts.get_text('preconsulta.checklist_title_personal'),
            reply_markup=keyboards.get_pathologies_keyboard('personal_history'),
            parse_mode=ParseMode.HTML
        )
        return AWAITING_PERSONAL_HISTORY_CHECKLIST
    else:
        context.user_data['personal_history'] = "No"
        return await ask_supplements(update, context)



# features/preconsulta/general_medical_handlers.py

# features/preconsulta/general_medical_handlers.py

async def show_medical_history_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Muestra el resumen de Antecedentes SOLO cuando hay texto libre para editar.
    Si no hay campos editables, pasa directamente a la siguiente sección.
    """
    ud = context.user_data

    # Lista de claves de los botones predefinidos de la checklist
    pathology_keys = {
        "diabetes", "tiroides", "asma", "alergias", "inmunologicas",
        "cardiovasculares", "respiratorias", "renales", "intestino_irritable"
    }

    # Lista para almacenar los botones de edición que se deben mostrar
    editable_fields = []

    # Comprobamos si se escribió texto libre para la Madre
    if any(item not in pathology_keys for item in ud.get('mother_history_selected', set())):
        editable_fields.append(('family_history_mother', 'Antecedentes (Madre)', 'other_prompt_mother'))

    # Comprobamos si se escribió texto libre para el Padre
    if any(item not in pathology_keys for item in ud.get('father_history_selected', set())):
        editable_fields.append(('family_history_father', 'Antecedentes (Padre)', 'other_prompt_father'))

    # Comprobamos si se escribió texto libre para el Paciente
    if any(item not in pathology_keys for item in ud.get('personal_history_selected', set())):
        editable_fields.append(('personal_history', 'Antecedentes (Personales)', 'other_prompt_personal'))

    # --- NUEVA LÓGICA: Si NO hay campos editables, pasamos directamente ---
    if not editable_fields:
        # No hay texto libre para editar, pasamos directamente a la siguiente sección
        return await ask_supplements(update, context)

    # --- SOLO mostramos el resumen si HAY campos editables ---
    summary_text = (
        "✍️ **Paso 2: Resumen de Antecedentes**\n\n"
        "Revisa los datos. Si necesitas corregir un texto que escribiste, aparecerá un botón para ello.\n\n"
        f"<b>Madre:</b> {escape_html(ud.get('family_history_mother', 'N/A'))}\n"
        f"<b>Padre:</b> {escape_html(ud.get('family_history_father', 'N/A'))}\n"
        f"<b>Personales:</b> {escape_html(ud.get('personal_history', 'N/A'))}"
    )

    # Generamos el teclado pasándole la lista de botones a crear
    reply_markup = get_med_history_summary_keyboard(editable_fields)

    # Lógica para editar el mensaje ancla
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=summary_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    else:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=context.user_data['anchor_message_id'],
            text=summary_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

    return AWAITING_SUMMARY_CONFIRMATION


async def handle_personal_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selection = query.data.split('_', 2)[-1]
    selected = context.user_data.get('personal_history_selected', set())

    if selection == 'done':
        # Guardamos la respuesta final
        context.user_data['personal_history'] = ", ".join(sorted(list(selected))) if selected else "Sí, no especificado."

        # --- ¡CAMBIO CLAVE! ---
        # Ahora, SIEMPRE mostramos el resumen, sin condiciones.
        return await show_medical_history_summary(update, context)

    elif selection == 'other':
        await query.edit_message_text(text=texts.get_text('preconsulta.other_prompt_personal'))
        return AWAITING_PERSONAL_HISTORY_TEXT

    # El resto de la lógica de selección de la checklist no cambia
    if selection in selected: selected.remove(selection)
    else: selected.add(selection)

    try:
        await query.edit_message_reply_markup(reply_markup=keyboards.get_pathologies_keyboard('personal_history', selected))
    except BadRequest as e:
        if "Message is not modified" not in str(e): logger.error(f"Error al actualizar teclado personal: {e}")
    return AWAITING_PERSONAL_HISTORY_CHECKLIST

async def receive_personal_other_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    other_text = update.message.text
    await update.message.delete()
    selected = context.user_data.get('personal_history_selected', set())
    selected.add(other_text)
    context.user_data['personal_history_selected'] = selected

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
        text=texts.get_text('preconsulta.checklist_title_personal'),
        reply_markup=keyboards.get_pathologies_keyboard('personal_history', selected)
    )
    return AWAITING_PERSONAL_HISTORY_CHECKLIST

async def ask_supplements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    question_text = texts.get_text('preconsulta.ask_supplements')
    await update.callback_query.edit_message_text(
        text=question_text,
        reply_markup=keyboards.get_yes_no_keyboard('supplements'),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_SUPPLEMENTS

async def handle_supplements_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data.endswith('_yes'):
        await query.edit_message_text(
            text=texts.get_text('preconsulta.supplements_prompt'),
            parse_mode=ParseMode.HTML
        )
        return AWAITING_SUPPLEMENTS_TEXT
    else:
        context.user_data['supplements'] = "No"
        return await ask_surgical_history(update, context)

async def receive_supplements_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['supplements'] = update.message.text
    await update.message.delete()
    return await ask_surgical_history(update, context)

async def ask_surgical_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query: await update.callback_query.answer()
    question_text = texts.get_text('preconsulta.ask_surgical_history')
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
        text=question_text,
        reply_markup=keyboards.get_yes_no_keyboard('surgical'),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_SURGICAL_HISTORY

async def handle_surgical_history_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data.endswith('_yes'):
        await query.edit_message_text(
            text=texts.get_text('preconsulta.surgical_history_prompt'),
            parse_mode=ParseMode.HTML
        )
        return AWAITING_SURGICAL_HISTORY_TEXT
    else:
        context.user_data['surgical_history'] = "No"
        return await ask_gyn_history_start(update, context)

async def receive_surgical_history_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['surgical_history'] = update.message.text
    await update.message.delete()
    return await ask_gyn_history_start(update, context)