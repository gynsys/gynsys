# /common/helpers.py
import html
import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

logger = logging.getLogger(__name__)

# --- FUNCIÓN DE ESCAPE ---
def escape_html(text: str) -> str:
    """
    Escapa caracteres especiales de HTML (<, >, &) para inyectar texto
    dinámico de forma segura en un mensaje con ParseMode.HTML.
    """
    if not isinstance(text, str):
        return ""
    return html.escape(text)

async def clear_patient_chat(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """
    Intenta borrar los mensajes guardados en el user_data de un paciente específico.
    Diseñado para ser llamado desde un contexto diferente (ej. el del admin).
    """
    # Usamos context.application.user_data para acceder a los datos de otro usuario
    patient_user_data = context.application.user_data.get(chat_id)

    if not patient_user_data:
        logger.info(f"No se encontró user_data para el paciente {chat_id}, no se puede limpiar.")
        return

    # Usamos la misma clave que ya defines en tu sistema de limpieza
    message_ids = patient_user_data.pop('messages_to_delete', [])

    if not message_ids:
        return

    logger.info(f"Limpieza remota: Intentando borrar {len(message_ids)} mensajes del chat {chat_id}")
    for message_id in message_ids:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            await asyncio.sleep(0.1)
        except BadRequest:
            # Ignoramos si el mensaje ya no existe
            pass
# --- FUNCIÓN DE BARRA DE PROGRESO ---
def generate_progress_bar(answers: list, total_questions: int) -> str:
    """
    Genera una barra de progreso con emojis y porcentaje para el test.
    """
    progress = []
    for answer in answers:
        progress.append('🟩' if answer == 'yes' else '🟥')

    remaining = total_questions - len(answers)
    progress.extend(['⬜️'] * remaining)

    percent = (len(answers) / total_questions) * 100 if total_questions > 0 else 0

    return f"{' '.join(progress)} {percent:.0f}% completado"

# --- FUNCIONES DE LIMPIEZA DE CONVERSACIÓN ---
async def add_message_to_cleanup(context: ContextTypes.DEFAULT_TYPE, message):
    """Añade el ID de un mensaje a la lista de limpieza en user_data."""
    if 'messages_to_delete' not in context.user_data:
        context.user_data['messages_to_delete'] = []
    if message and hasattr(message, 'message_id'):
        if message.message_id not in context.user_data['messages_to_delete']:
            context.user_data['messages_to_delete'].append(message.message_id)

async def cleanup_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Borra todos los mensajes intermedios guardados en una conversación."""
    if update.message:
        await add_message_to_cleanup(context, update.message)

    message_ids_to_delete = context.user_data.pop('messages_to_delete', [])

    if not message_ids_to_delete:
        return

    logger.info(f"Iniciando limpieza de {len(message_ids_to_delete)} mensajes para el chat {update.effective_chat.id}")

    for message_id in message_ids_to_delete:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
            await asyncio.sleep(0.1)
        except BadRequest as e:
            if "message to delete not found" in str(e):
                logger.warning(f"Mensaje {message_id} ya había sido borrado.")
            else:
                logger.error(f"Error al borrar mensaje {message_id}: {e}")

    logger.info("Limpieza de mensajes completada.")