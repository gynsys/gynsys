"""
Handlers para flujo ginecológico: Ciclos, menstruación.
Interacción con Telegram y contexto del flujo.
"""
import logging
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def decide_if_ask_frequency(update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """
    Lee si el ciclo fue marcado como 'Regulares' o 'Irregulares' y
    devuelve el ID del siguiente nodo correspondiente.
    """
    if context.user_data.get('gyn_cycles') == 'Regulares':
        return node['next_if_regular']
    else:
        return node['next_if_irregular']


async def combine_irregular_cycle_info(update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Formatea el texto para ciclos irregulares (solo con duración)."""
    duration = context.user_data.get('gyn_cycles_duration', 'N/A')
    context.user_data['gyn_cycles'] = f"Irregulares. Duración: {duration}."
    return node.get('next_node')


async def combine_regular_cycle_info(update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Formatea el texto para ciclos regulares (con duración y frecuencia)."""
    duration = context.user_data.get('gyn_cycles_duration', 'N/A')
    frequency = context.user_data.get('gyn_cycles_frequency', 'N/A')
    context.user_data['gyn_cycles'] = f"Regulares. Duración: {duration}. Frecuencia: {frequency}."
    return node.get('next_node')


async def combine_dysmenorrhea_info(update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Formatea el texto para dismenorrea."""
    scale_value = context.user_data.get('gyn_dysmenorrhea_scale_value', 'N/A')
    context.user_data['gyn_dysmenorrhea'] = f"Sí, intensidad: {scale_value}/10"
    return node.get('next_node')

