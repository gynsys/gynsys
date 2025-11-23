"""
Handlers para hábitos: Actividad física, hábitos.
Interacción con Telegram y contexto del flujo.
"""
import logging
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def combine_activity_info(update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Formatea el texto para actividad física."""
    days = context.user_data.get('habits_activity_days', 'N/A')
    duration = context.user_data.get('habits_activity_duration', 'N/A')
    habit_duration = context.user_data.get('habits_activity_habit_duration', 'N/A')
    goal = context.user_data.get('habits_activity_goal', 'N/A')
    summary = (
        f"Sí. Frecuencia: {days} días/semana, Duración: {duration} min. "
        f"Hábito: {habit_duration}. Objetivo: {goal}."
    )
    context.user_data['habits_physical_activity'] = summary
    
    # Limpiar variables temporales
    keys_to_pop = [
        'habits_activity_days',
        'habits_activity_duration',
        'habits_activity_habit_duration',
        'habits_activity_goal'
    ]
    for key in keys_to_pop:
        context.user_data.pop(key, None)
    
    return node.get('next_node')

