"""
Middleware para rastrear mensajes enviados/recibidos
Se ejecuta en todos los handlers para actualizar métricas
"""

from telegram import Update
from telegram.ext import ContextTypes
from utils.health_metrics import get_metrics
import logging

logger = logging.getLogger(__name__)


async def track_message_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Middleware que rastrea mensajes entrantes
    Debe ser registrado como primer handler con group=-1
    """
    metrics = get_metrics()
    
    if update.message:
        metrics.log_message_received()
    
    # Continuar con el siguiente handler
    return


async def track_outgoing_message(original_method):
    """
    Decorator para rastrear mensajes salientes
    Envuelve métodos como send_message, edit_message_text, etc.
    """
    async def wrapper(*args, **kwargs):
        try:
            result = await original_method(*args, **kwargs)
            metrics = get_metrics()
            metrics.log_message_sent()
            return result
        except Exception as e:
            raise e
    return wrapper
