# features/quiz/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_start_quiz_keyboard():
    """Teclado para la pantalla de bienvenida del quiz"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🕹️ Jugar", callback_data="quiz_start_game")],
        [InlineKeyboardButton("🏠", callback_data="main_menu")]
    ])

def get_quiz_question_keyboard():
    """Teclado para responder una pregunta del quiz"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👍 Verdad", callback_data="quiz_answer_true"),
            InlineKeyboardButton("👎 Mito", callback_data="quiz_answer_false")
        ],
        [InlineKeyboardButton("❌ Cancelar", callback_data="quiz_cancel")]
    ])

def get_quiz_final_keyboard():
    """Teclado al finalizar el quiz"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧩 Jugar de nuevo", callback_data="quiz_start_game")],
        [InlineKeyboardButton("🏠 Inicio", callback_data="main_menu")]
    ])

def get_quiz_explanation_keyboard():
    """Teclado para mostrar después de una respuesta incorrecta"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👍 Entendido", callback_data="quiz_understood")]
    ])

