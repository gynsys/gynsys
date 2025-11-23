import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from database import preconsulta_db
from common.decorators import admin_required
from utils.role_manager import RoleManager
from config import DB_PATH

logger = logging.getLogger(__name__)

# Helper para obtener doctor_id (multi-tenant)
role_manager = RoleManager(DB_PATH)

async def _get_doctor_id(update: Update) -> int:
    """Obtiene el doctor_id del usuario actual."""
    user_id = update.effective_user.id
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    if doctor:
        return doctor[0]
    return None

@admin_required
async def download_summary_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Recupera el file_id de un PDF RESUMIDO y lo envía al admin.
    """
    query = update.callback_query
    await query.answer("📥 Preparando tu informe resumido...")
    
    try:
        # El formato es: download_summary_pdf_{history_id} o download_summary_pdf_{history_id}_suffix
        parts = query.data.split('_')
        history_id = int(parts[3])  # El history_id está en la posición 3
    except (ValueError, IndexError):
        await query.answer("❌ Error: ID de historia no válido.", show_alert=True)
        return

    # Usamos la nueva clave de caché
    pdf_file_id = context.bot_data.get('summary_pdf_file_ids', {}).get(history_id)
    
    if not pdf_file_id:
        await query.answer("❌ No se pudo encontrar el PDF. Intenta re-generarlo.", show_alert=True)
        return

    try:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=pdf_file_id,
            caption=f"Informe Médico Resumido para la historia #{history_id}."
        )
    except Exception as e:
        logger.error(f"No se pudo enviar el PDF resumido con file_id para history {history_id}: {e}")
        await query.answer("❌ Hubo un error al enviar el archivo.", show_alert=True)


@admin_required
async def send_summary_to_patient(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envía el PDF RESUMIDO al paciente."""
    query = update.callback_query
    await query.answer()

    try:
        # El formato es: send_summary_to_patient_{history_id} o send_summary_to_patient_{history_id}_suffix
        parts = query.data.split('_')
        history_id = int(parts[4])  # El history_id está en la posición 4 (send_summary_to_patient_{id})
    except (ValueError, IndexError):
        await query.answer("❌ Error: ID de historia no válido.", show_alert=True)
        return

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.answer("❌ Error: No se pudo identificar tu perfil de médico.", show_alert=True)
        return
    # Usamos la nueva clave de caché
    pdf_file_id = context.bot_data.get('summary_pdf_file_ids', {}).get(history_id)
    history_details = await preconsulta_db.get_history_details(history_id, doctor_id)

    if not history_details or not pdf_file_id:
        await query.answer("❌ Error: No se pudo encontrar la historia o el PDF.", show_alert=True)
        return

    patient_id = history_details.get('user_id')
    
    # Obtener nombre del doctor
    doctor = await role_manager.get_doctor_by_id(doctor_id)
    doctor_name = doctor[1] if doctor else "tu médico"
    
    try:
        # Enviar el PDF al paciente
        await context.bot.send_document(
            chat_id=patient_id,
            document=pdf_file_id,
            caption=f"Hola, {doctor_name} te envía un resumen de tu informe médico."
        )
        
        # Mostrar mensaje autodestructivo de éxito
        await query.answer("✔️ Informe enviado con éxito", show_alert=False)
        
        # Editar el mensaje brevemente para dar feedback visual
        original_text = query.message.text
        original_markup = query.message.reply_markup
        
        try:
            await query.edit_message_text("✔️ Informe enviado con éxito")
            # Esperar 2 segundos y restaurar
            await asyncio.sleep(2)
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=query.message.message_id,
                text=original_text,
                reply_markup=original_markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Error al mostrar mensaje autodestructivo: {e}")
            
    except Exception as e:
        logger.error(f"Error al enviar PDF resumido al paciente {patient_id}: {e}")
        await query.answer("❌ Hubo un error al intentar enviar el informe.", show_alert=True)


def register(app: Application):
    """Registra los handlers específicos para las acciones de los PDF resumidos."""
    app.add_handler(CallbackQueryHandler(download_summary_pdf, pattern=r'^download_summary_pdf_'))
    app.add_handler(CallbackQueryHandler(send_summary_to_patient, pattern=r'^send_summary_to_patient_'))