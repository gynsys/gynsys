"""
Workflow para FAQs – refactor multi-tenant.
Mismo nombre de archivo para no romper imports.
"""
import logging
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from common.context_manager import get_tenant_id
from .faq_service import add_faq, update_faq, delete_faq, get_faq, list_faqs
from .keyboards import faqs_for_action_keyboard   # mismo nombre

logger = logging.getLogger(__name__)

class FAQWorkflow:
    @staticmethod
    async def get_bot_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
        return await get_tenant_id(update, context)

    @staticmethod
    async def handle_add_workflow(update: Update, context: ContextTypes.DEFAULT_TYPE, q: str, a: str) -> Dict[str, Any]:
        bot_id = await FAQWorkflow.get_bot_id(update, context)
        if not bot_id:
            return {"success": False, "error": "No se pudo determinar el bot"}
        faq_id = await add_faq(bot_id, q, a)
        return {"success": bool(faq_id), "faq_id": faq_id}

    @staticmethod
    async def handle_update_workflow(update: Update, context: ContextTypes.DEFAULT_TYPE, faq_id: int, q: Optional[str] = None, a: Optional[str] = None) -> Dict[str, Any]:
        bot_id = await FAQWorkflow.get_bot_id(update, context)
        if not bot_id:
            return {"success": False, "error": "No se pudo determinar el bot"}
        ok = await update_faq(faq_id, bot_id, q, a)
        return {"success": ok}

    @staticmethod
    async def handle_delete_workflow(update: Update, context: ContextTypes.DEFAULT_TYPE, faq_id: int) -> Dict[str, Any]:
        bot_id = await FAQWorkflow.get_bot_id(update, context)
        if not bot_id:
            return {"success": False, "error": "No se pudo determinar el bot"}
        ok = await delete_faq(faq_id, bot_id)
        return {"success": ok}

    @staticmethod
    async def handle_get_workflow(update: Update, context: ContextTypes.DEFAULT_TYPE, faq_id: int) -> Dict[str, Any]:
        bot_id = await FAQWorkflow.get_bot_id(update, context)
        if not bot_id:
            return {"success": False, "error": "No se pudo determinar el bot"}
        faq = await get_faq(faq_id, bot_id)
        if not faq:
            return {"success": False, "error": "FAQ no encontrada o no pertenece a este bot"}
        return {"success": True, "faq": faq}

    @staticmethod
    async def handle_list_workflow(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str = "modify") -> Dict[str, Any]:
        bot_id = await FAQWorkflow.get_bot_id(update, context)
        if not bot_id:
            return {"success": False, "error": "No se pudo determinar el bot"}
        items = await list_faqs(bot_id)
        if not items:
            return {"success": False, "error": f"No hay FAQs para {action}"}
        kb = await faqs_for_action_keyboard(items, action)
        return {"success": True, "keyboard": kb}

class WorkflowState:
    AWAITING_QUESTION = 1
    AWAITING_ANSWER = 2
    AWAITING_MOD_QUESTION = 3
    AWAITING_MOD_ANSWER = 4