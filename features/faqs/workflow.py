"""
Workflow para operaciones CRUD de FAQs.
Arquitectura limpia que separa responsabilidades por tipo de usuario:
- Superadmin: Gestiona FAQs de todos los tenants
- Tenants (Doctores): Gestionan sus propias FAQs
- Usuarios: Solo visualizan (manejado en user_handlers.py)
"""
import logging
from typing import Optional, Dict, Any, Callable
from telegram import Update, CallbackQuery, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from common.context_manager import get_tenant_id
from .faq_service import (
    add_faq_direct,
    update_faq_direct,
    get_faq_details_direct,
    get_all_faqs_for_bot
)
from . import keyboards as admin_keyboards

logger = logging.getLogger(__name__)


class FAQWorkflow:
    """Workflow centralizado para operaciones CRUD de FAQs"""
    
    @staticmethod
    async def get_bot_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
        """Obtiene el bot_id validado"""
        try:
            bot_id = await get_tenant_id(update, context)
            if not bot_id:
                logger.warning(f"No se pudo obtener bot_id para usuario {update.effective_user.id}")
            return bot_id
        except Exception as e:
            logger.error(f"Error obteniendo bot_id: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def create_fake_update(
        update: Update,
        callback_data: str,
        message=None
    ) -> Update:
        """Crea un Update simulado para redirecciones"""
        fake_query = CallbackQuery(
            id="fake_query_id",
            from_user=update.effective_user,
            chat_instance="fake_chat_instance",
            data=callback_data,
            message=message
        )
        return Update(
            update_id=update.update_id,
            callback_query=fake_query
        )
    
    @staticmethod
    async def redirect_to_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Redirige al hub de FAQs"""
        from .admin_handlers import faqs_hub
        fake_update = await FAQWorkflow.create_fake_update(
            update,
            "faqs_admin_hub",
            update.effective_message
        )
        await faqs_hub(fake_update, context)
    
    @staticmethod
    async def redirect_to_list(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        action: str = "modify",
        message=None
    ):
        """Redirige a la lista de FAQs para una acción específica"""
        from .admin_handlers import list_items_for_action
        fake_update = await FAQWorkflow.create_fake_update(
            update,
            f"faq_{action}_list",
            message
        )
        await list_items_for_action(fake_update, context)
    
    @staticmethod
    async def handle_add_workflow(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        question: str,
        answer: str
    ) -> Dict[str, Any]:
        """
        Workflow para agregar una FAQ.
        
        Returns:
            Dict con 'success' (bool) y 'faq_id' (int) o 'error' (str)
        """
        bot_id = await FAQWorkflow.get_bot_id(update, context)
        if not bot_id:
            return {'success': False, 'error': 'No se pudo determinar el bot_id'}
        
        try:
            faq_id = await add_faq_direct(bot_id, question, answer)
            if not faq_id:
                return {'success': False, 'error': 'No se pudo crear la FAQ'}
            
            logger.info(f"✅ FAQ creada: id={faq_id}, bot_id={bot_id}")
            return {'success': True, 'faq_id': faq_id}
        except Exception as e:
            logger.error(f"❌ Error en handle_add_workflow: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    async def handle_update_workflow(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        faq_id: int,
        question: Optional[str] = None,
        answer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Workflow para actualizar una FAQ.
        
        Returns:
            Dict con 'success' (bool) y 'error' (str) si falla
        """
        bot_id = await FAQWorkflow.get_bot_id(update, context)
        if not bot_id:
            return {'success': False, 'error': 'No se pudo determinar el bot_id'}
        
        try:
            # Validar que la FAQ existe y pertenece al bot
            existing = await get_faq_details_direct(faq_id, bot_id)
            if not existing:
                return {'success': False, 'error': 'FAQ no encontrada o no pertenece a este bot'}
            
            # Si no se proporcionaron valores, mantener los originales
            final_question = question if question is not None else existing['title']
            final_answer = answer if answer is not None else existing['content']
            
            success = await update_faq_direct(faq_id, bot_id, final_question, final_answer)
            if not success:
                return {'success': False, 'error': 'No se pudo actualizar la FAQ'}
            
            logger.info(f"✅ FAQ actualizada: id={faq_id}, bot_id={bot_id}")
            return {'success': True}
        except Exception as e:
            logger.error(f"❌ Error en handle_update_workflow: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    async def handle_delete_workflow(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        faq_id: int
    ) -> Dict[str, Any]:
        """
        Workflow para eliminar una FAQ.
        
        Returns:
            Dict con 'success' (bool) y 'error' (str) si falla
        """
        bot_id = await FAQWorkflow.get_bot_id(update, context)
        if not bot_id:
            return {'success': False, 'error': 'No se pudo determinar el bot_id'}
        
        try:
            # Validar que la FAQ existe y pertenece al bot
            existing = await get_faq_details_direct(faq_id, bot_id)
            if not existing:
                return {'success': False, 'error': 'FAQ no encontrada o no pertenece a este bot'}
            
            # Eliminar usando content_db (ya funciona)
            from database import content_db
            success = await content_db.delete_item(faq_id, 'faqs')
            
            if not success:
                return {'success': False, 'error': 'No se pudo eliminar la FAQ'}
            
            logger.info(f"✅ FAQ eliminada: id={faq_id}, bot_id={bot_id}")
            return {'success': True}
        except Exception as e:
            logger.error(f"❌ Error en handle_delete_workflow: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    async def handle_get_workflow(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        faq_id: int
    ) -> Dict[str, Any]:
        """
        Workflow para obtener detalles de una FAQ.
        
        Returns:
            Dict con 'success' (bool), 'faq' (dict) o 'error' (str)
        """
        bot_id = await FAQWorkflow.get_bot_id(update, context)
        if not bot_id:
            return {'success': False, 'error': 'No se pudo determinar el bot_id'}
        
        try:
            faq = await get_faq_details_direct(faq_id, bot_id)
            if not faq:
                return {'success': False, 'error': 'FAQ no encontrada'}
            
            return {'success': True, 'faq': faq}
        except Exception as e:
            logger.error(f"❌ Error en handle_get_workflow: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    async def handle_list_workflow(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        action: str = "modify"
    ) -> Dict[str, Any]:
        """
        Workflow para listar FAQs para una acción específica.
        
        Returns:
            Dict con 'success' (bool), 'keyboard' (InlineKeyboardMarkup) o 'error' (str)
        """
        bot_id = await FAQWorkflow.get_bot_id(update, context)
        if not bot_id:
            return {'success': False, 'error': 'No se pudo determinar el bot_id'}
        
        try:
            keyboard = await admin_keyboards.get_faqs_for_action_keyboard(bot_id, action)
            if not keyboard:
                return {'success': False, 'error': f'No hay FAQs para {action}'}
            
            return {'success': True, 'keyboard': keyboard}
        except Exception as e:
            logger.error(f"❌ Error en handle_list_workflow: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}


class WorkflowState:
    """Estados del workflow para conversaciones - Usando enteros para compatibilidad con ConversationHandler"""
    IDLE = 0
    AWAITING_QUESTION = 1
    AWAITING_ANSWER = 2
    AWAITING_MOD_QUESTION = 3
    AWAITING_MOD_ANSWER = 4
    AWAITING_HEADER = 5

