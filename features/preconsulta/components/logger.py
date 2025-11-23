# components/logger.py

import logging
from typing import Any, Dict, Optional
from telegram.ext import ContextTypes
from telegram import Update

# Configurar el logger principal
logger = logging.getLogger(__name__)

class ConversationLogger:
    """Logger especializado para seguimiento de conversaciones y estados"""
    
    @staticmethod
    def log_conversation_state(context: ContextTypes.DEFAULT_TYPE, operation: str, module: str = ""):
        """Registra el estado actual de la conversación y user_data"""
        current_state = context.user_data.get('__conversation_state', 'NO_STATE')
        editing_history_id = context.user_data.get('editing_history_id', 'NO_HISTORY_ID')
        editing_field = context.user_data.get('editing_field', 'NO_FIELD')
        
        module_prefix = f"[{module}] " if module else ""
        
        logger.info(f"🔍 {module_prefix}CONVERSATION_STATE [{operation}] - State: {current_state}, History: {editing_history_id}, Field: {editing_field}")
        logger.info(f"🔍 {module_prefix}USER_DATA_KEYS: {list(context.user_data.keys())}")

    @staticmethod
    def log_handler_execution(handler_name: str, update: Update, module: str = ""):
        """Registra la ejecución de un handler"""
        module_prefix = f"[{module}] " if module else ""
        
        if update.callback_query:
            logger.info(f"📨 {module_prefix}HANDLER [{handler_name}] - Callback: {update.callback_query.data}")
        elif update.message:
            logger.info(f"📨 {module_prefix}HANDLER [{handler_name}] - Message: {update.message.text[:100] if update.message.text else 'NO_TEXT'}")

    @staticmethod
    def log_function_call(function_name: str, module: str = "", **kwargs):
        """Registra la llamada a una función con parámetros opcionales"""
        module_prefix = f"[{module}] " if module else ""
        params = f" - Params: {kwargs}" if kwargs else ""
        logger.info(f"🚀 {module_prefix}FUNCTION_CALL [{function_name}]{params}")

    @staticmethod
    def log_success(operation: str, details: str = "", module: str = ""):
        """Registra una operación exitosa"""
        module_prefix = f"[{module}] " if module else ""
        details_text = f" - {details}" if details else ""
        logger.info(f"✅ {module_prefix}SUCCESS [{operation}]{details_text}")

    @staticmethod
    def log_error(operation: str, error: Exception, details: str = "", module: str = ""):
        """Registra un error"""
        module_prefix = f"[{module}] " if module else ""
        details_text = f" - {details}" if details else ""
        logger.error(f"❌ {module_prefix}ERROR [{operation}] - {error}{details_text}")

    @staticmethod
    def log_warning(operation: str, details: str = "", module: str = ""):
        """Registra una advertencia"""
        module_prefix = f"[{module}] " if module else ""
        details_text = f" - {details}" if details else ""
        logger.warning(f"⚠️ {module_prefix}WARNING [{operation}]{details_text}")

    @staticmethod
    def log_info(message: str, module: str = ""):
        """Registra un mensaje informativo"""
        module_prefix = f"[{module}] " if module else ""
        logger.info(f"ℹ️ {module_prefix}{message}")

    @staticmethod
    def log_debug(message: str, module: str = ""):
        """Registra un mensaje de debug"""
        module_prefix = f"[{module}] " if module else ""
        logger.debug(f"🐛 {module_prefix}{message}")

# Instancia global para uso fácil
conv_logger = ConversationLogger()

# Funciones de conveniencia para uso rápido
def log_state(context: ContextTypes.DEFAULT_TYPE, operation: str, module: str = ""):
    """Función rápida para log del estado"""
    conv_logger.log_conversation_state(context, operation, module)

def log_handler(handler_name: str, update: Update, module: str = ""):
    """Función rápida para log de handlers"""
    conv_logger.log_handler_execution(handler_name, update, module)

def log_func(function_name: str, module: str = "", **kwargs):
    """Función rápida para log de llamadas a funciones"""
    conv_logger.log_function_call(function_name, module, **kwargs)

def log_ok(operation: str, details: str = "", module: str = ""):
    """Función rápida para log de éxito"""
    conv_logger.log_success(operation, details, module)

def log_err(operation: str, error: Exception, details: str = "", module: str = ""):
    """Función rápida para log de error"""
    conv_logger.log_error(operation, error, details, module)

def log_warn(operation: str, details: str = "", module: str = ""):
    """Función rápida para log de advertencia"""
    conv_logger.log_warning(operation, details, module)

def log_msg(message: str, module: str = ""):
    """Función rápida para log de mensaje informativo"""
    conv_logger.log_info(message, module)