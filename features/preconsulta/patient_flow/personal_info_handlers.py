# features/preconsulta/patient_flow/personal_info_handlers.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
# ¡IMPORTANTE! Volvemos a necesitar AWAITING_GENERIC_INPUT aquí.
from ..states import AWAITING_GENERIC_INPUT

logger = logging.getLogger(__name__)



def get_personal_info_summary_keyboard(node_id: str):
    """Crea el teclado para el resumen, con opciones de edición y continuación."""
    keyboard = [
        [InlineKeyboardButton("✏️ Nombre", callback_data=f"edit_full_name")],
        [InlineKeyboardButton("✏️ Edad", callback_data=f"edit_age")],
        [InlineKeyboardButton("✏️ C.I.", callback_data=f"edit_ci")],
        [InlineKeyboardButton("✏️ Teléfono", callback_data=f"edit_phone")],
        [InlineKeyboardButton("✏️ Dirección", callback_data=f"edit_address")],
        [InlineKeyboardButton("✏️ Ocupación", callback_data=f"edit_occupation")],
        # El callback_data de continuar debe ser único para que process_input lo reconozca
        [InlineKeyboardButton("✅ Todo Correcto, Continuar", callback_data=f"{node_id}_continue")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def show_personal_info_summary(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """
    Muestra el resumen de la información personal con su teclado y
    ESPERA la respuesta del usuario.
    """
    if update.callback_query:
        await update.callback_query.answer()

    user_data = context.user_data
    def clean_html(text):
        import re
        return re.sub(r'<[^>]+>', '', text) if isinstance(text, str) else text

    summary_text = (
        "<b>Resumen de tu Información Personal, por favor verifica tus datos, es el momento de corregir de haber cometido algun error, de lo contrario puedes continuar:</b>\n\n"
        f"<b>Nombre:</b> {user_data.get('full_name', 'N/A')}\n"
        f"<b>Edad:</b> {user_data.get('age', 'N/A')}\n"
        f"<b>C.I.:</b> {user_data.get('ci', 'N/A')}\n"
        f"<b>Teléfono:</b> {user_data.get('phone', 'N/A')}\n"
        f"<b>Dirección:</b> {user_data.get('address', 'N/A')}\n"
        f"<b>Ocupación:</b> {user_data.get('occupation', 'N/A')}\n"
    )

    # Antecedentes familiares y personales
    mother = clean_html(user_data.get('family_history_mother', 'No especificado'))
    mother_other = clean_html(user_data.get('family_history_mother_other', ''))
    father = clean_html(user_data.get('family_history_father', 'No especificado'))
    father_other = clean_html(user_data.get('family_history_father_other', ''))
    personal = clean_html(user_data.get('personal_history', 'No especificado'))
    personal_other = clean_html(user_data.get('personal_history_other', ''))

    summary_text += f"\n<b>Antecedentes familiares:</b>\nMadre: {mother}"
    if mother_other:
        summary_text += f"\nOtra patología madre: {mother_other}"
    summary_text += f"\nPadre: {father}"
    if father_other:
        summary_text += f"\nOtra patología padre: {father_other}"
    summary_text += f"\nPersonales: {personal}"
    if personal_other:
        summary_text += f"\nOtras enfermedades/alergias: {personal_other}"

    current_node_id = context.user_data.get('current_node_id') # Será 'SHOW_SUMMARY'

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=user_data['anchor_message_id'],
        text=summary_text,
        reply_markup=get_personal_info_summary_keyboard(current_node_id),
        parse_mode=ParseMode.HTML
    )

    # Devolvemos el estado de espera. La acción termina aquí. El motor se detiene.
    return AWAITING_GENERIC_INPUT