# /features/test/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from common.keyboards import get_return_to_main_menu_keyboard as common_return_keyboard

# --- FUNCIÓN CORREGIDA ---
# Hemos eliminado el parámetro 'bot_id' porque no se utiliza.
def get_start_test_keyboard():
    """Crea el teclado para iniciar el test."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Comenzar", callback_data='begin_test')],
        [InlineKeyboardButton("🏠 Menú Principal", callback_data='main_menu')]
    ])

# --- FUNCIÓN CORREGIDA ---
# También eliminamos 'bot_id' de aquí por la misma razón.
def get_test_question_keyboard():
    """Crea el teclado con las opciones de respuesta para una pregunta del test."""
    keyboard = [
        [
            InlineKeyboardButton("👍 Sí", callback_data='test_answer_yes'),
            InlineKeyboardButton("👎 No", callback_data='test_answer_no')
        ],
        [InlineKeyboardButton("❌ Cancelar Test", callback_data='cancel_test')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_return_to_main_menu_keyboard():
    """
    Wrapper para la función común, por si en el futuro queremos
    un texto específico para el test.
    """
    return common_return_keyboard()