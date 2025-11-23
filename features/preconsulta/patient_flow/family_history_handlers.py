# features/preconsulta/family_history_handlers.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from telegram.constants import ParseMode
from features.preconsulta.components import keyboards
from .general_medical_handlers import ask_personal_history_bool
from common import texts # Importamos el módulo de textos
from features.preconsulta.states import *

logger = logging.getLogger(__name__)



async def ask_mother_history_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Función de entrada al módulo. Pregunta por las patologías de la madre."""
    question_text = (
        f"{texts.get_text('preconsulta.section_medical_history')}\n\n"
        f"{texts.get_text('preconsulta.ask_mother_history')}"
    )

    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=context.user_data['anchor_message_id'],
            text=question_text,
            reply_markup=keyboards.get_yes_no_keyboard('mother_history_bool'),
            parse_mode=ParseMode.HTML
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error en ask_mother_history_bool: {e}")
    return AWAITING_MOTHER_HISTORY_BOOL


async def handle_mother_history_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la respuesta Sí/No para la madre y pasa a la checklist o al padre."""
    query = update.callback_query
    await query.answer()
    if query.data.endswith('_yes'):
        context.user_data['mother_history_selected'] = set()
        await query.edit_message_text(
            text=texts.get_text('preconsulta.checklist_title_mother'),
            reply_markup=keyboards.get_pathologies_keyboard('mother_history'),
            parse_mode=ParseMode.HTML
        )
        return AWAITING_MOTHER_HISTORY_CHECKLIST
    else:
        context.user_data['family_history_mother'] = "No"
        return await ask_father_history_bool(update, context)


async def handle_mother_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selection = query.data.split('_', 2)[-1]
    selected = context.user_data.get('mother_history_selected', set())

    if selection == 'done':
        final_response = ", ".join(sorted(list(selected))) if selected else "Sí, no especificado"
        context.user_data['family_history_mother'] = final_response
        return await ask_father_history_bool(update, context)
    elif selection == 'other':
        await query.edit_message_text(
            text=texts.get_text('preconsulta.other_prompt_mother'),
            parse_mode=ParseMode.HTML
        )
        return AWAITING_MOTHER_HISTORY_TEXT

    if selection in selected: selected.remove(selection)
    else: selected.add(selection)
    context.user_data['mother_history_selected'] = selected
    try:
        await query.edit_message_reply_markup(reply_markup=keyboards.get_pathologies_keyboard('mother_history', selected))
    except BadRequest as e:
        if "Message is not modified" not in str(e): logger.error(f"Error al actualizar teclado madre: {e}")
    return AWAITING_MOTHER_HISTORY_CHECKLIST


async def receive_mother_other_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    other_text = update.message.text
    await update.message.delete()
    selected = context.user_data.get('mother_history_selected', set())
    selected.add(other_text)
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
        text=texts.get_text('preconsulta.checklist_title_mother'),
        reply_markup=keyboards.get_pathologies_keyboard('mother_history', selected),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_MOTHER_HISTORY_CHECKLIST


async def ask_father_history_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    question_text = texts.get_text('preconsulta.ask_father_history')
    await query.edit_message_text(
        text=question_text,
        reply_markup=keyboards.get_yes_no_keyboard('father_history_bool'),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_FATHER_HISTORY_BOOL


async def handle_father_history_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data.endswith('_yes'):
        context.user_data['father_history_selected'] = set()
        await query.edit_message_text(
            text=texts.get_text('preconsulta.checklist_title_father'),
            reply_markup=keyboards.get_pathologies_keyboard('father_history'),
            parse_mode=ParseMode.HTML
        )
        return AWAITING_FATHER_HISTORY_CHECKLIST
    else:
        context.user_data['family_history_father'] = "No"
        return await ask_personal_history_bool(update, context)


async def handle_father_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selection = query.data.split('_', 2)[-1]
    selected = context.user_data.get('father_history_selected', set())

    if selection == 'done':
        final_response = ", ".join(sorted(list(selected))) if selected else "Sí, no especificado"
        context.user_data['family_history_father'] = final_response
        return await ask_personal_history_bool(update, context)
    elif selection == 'other':
        await query.edit_message_text(
            text=texts.get_text('preconsulta.other_prompt_father'),
            parse_mode=ParseMode.HTML
        )
        return AWAITING_FATHER_HISTORY_TEXT

    if selection in selected: selected.remove(selection)
    else: selected.add(selection)
    context.user_data['father_history_selected'] = selected
    try:
        await query.edit_message_reply_markup(reply_markup=keyboards.get_pathologies_keyboard('father_history', selected))
    except BadRequest as e:
        if "Message is not modified" not in str(e): logger.error(f"Error al actualizar teclado padre: {e}")
    return AWAITING_FATHER_HISTORY_CHECKLIST


async def receive_father_other_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    other_text = update.message.text
    await update.message.delete()
    selected = context.user_data.get('father_history_selected', set())
    selected.add(other_text)
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
        text=texts.get_text('preconsulta.checklist_title_father'),
        reply_markup=keyboards.get_pathologies_keyboard('father_history', selected),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_FATHER_HISTORY_CHECKLIST