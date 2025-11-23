"""
Handlers para ciclo de vida: Finalización y guardado de historia.
Interacción con Telegram y contexto del flujo.
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest
from common import texts
from database import preconsulta_db
from ..services.history_saver import build_history_data
# Import local dentro de la función para evitar import circular

logger = logging.getLogger(__name__)


async def check_if_pregnant_for_fertility(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """
    Decide si se debe preguntar sobre la intención de fertilidad basado en el
    contexto de actividad sexual y tipo de consulta.
    """
    # Import local para evitar importación circular
    from ...patient_flow.generic_flow_engine import render_node
    
    is_sexually_active = context.user_data.get('sexually_active', '').lower() == 'sí'
    is_prenatal_consultation = context.user_data.get('consultation_type') == 'Prenatal'

    if is_sexually_active and not is_prenatal_consultation:
        logger.info("Usuario activo y no prenatal. Preguntando sobre fertilidad.")
        return await render_node(update, context, node['next_if_ask_fertility'])
    else:
        logger.info("Usuario no activo o en consulta prenatal. Saltando pregunta de fertilidad.")
        return await render_node(update, context, node['next_if_skip_fertility'])


async def finish_preconsultation(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """
    Recopila, formatea y guarda los datos de la preconsulta en la base de datos.
    Luego, notifica al usuario y finaliza la conversación.
    """
    user_data = context.user_data
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    doctor_id = user_data.get('doctor_id')
    
    if not doctor_id:
        logger.error(f"No se encontró doctor_id en user_data para el usuario {user_id}. No se puede guardar la historia.")
        await context.bot.send_message(
            chat_id=chat_id,
            text="Error: No se pudo identificar tu médico. Por favor, contacta al soporte."
        )
        return ConversationHandler.END

    logger.info(f"Finalizando preconsulta para el usuario {user_id} con doctor_id {doctor_id}.")

    # Construir datos de historia usando el servicio
    history_data = build_history_data(user_data, user_id, doctor_id)

    # Guardar en la base de datos
    history_id = await preconsulta_db.save_history(history_data)

    # Borrar mensaje "ancla" de la preconsulta
    if anchor_id := user_data.get('anchor_message_id'):
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=anchor_id)
        except BadRequest as e:
            logger.warning(f"No se pudo borrar el mensaje ancla {anchor_id}: {e}")

    # Lógica de UI final
    if history_id:
        # Enviar mensaje de éxito
        final_message = await context.bot.send_message(
            chat_id=chat_id,
            text=texts.get_text("preconsulta.end_message"),
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(4)
        
        # Borrar mensaje de éxito
        try:
            await final_message.delete()
        except BadRequest:
            pass
        
        # Mostrar menú principal del paciente
        from features.patient_menu.patient_handler import patient_main_menu
        from utils.role_manager import RoleManager
        from config import DB_PATH
        role_manager = RoleManager(DB_PATH)
        assigned_doctor = await role_manager.get_assigned_doctor(user_id)
        if assigned_doctor:
            class FakeUpdate:
                def __init__(self, chat_id, effective_user):
                    self.effective_chat = type('obj', (object,), {'id': chat_id})()
                    self.effective_user = effective_user
                    self.message = None
                    self.callback_query = None
            
            fake_update = FakeUpdate(chat_id, update.effective_user)
            await patient_main_menu(fake_update, context, assigned_doctor[0])
    else:
        logger.error(f"FALLO al guardar la preconsulta para el usuario {user_id}.")
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Hubo un problema al guardar tu información. Por favor, intenta de nuevo o contacta a soporte."
        )

    # Finalizar
    context.user_data.clear()
    return "END_CONVERSATION"

