# features/quiz/user_handlers.py
import logging
import json
import random
import os
from pathlib import Path
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, ConversationHandler, CallbackQueryHandler, ContextTypes
)
from telegram.error import BadRequest, TimedOut
from telegram.constants import ParseMode
from common.helpers import escape_html
from common.context_manager import get_tenant_id
from database import extra_modules_db
from utils.role_manager import RoleManager
from config import DB_PATH
from handlers.callback_router import handle_all_callbacks
from . import keyboards

logger = logging.getLogger(__name__)
role_manager = RoleManager(DB_PATH)

# Estados del ConversationHandler
(WAITING_TO_START, PLAYING_QUIZ, SHOWING_EXPLANATION) = range(3)

# Cargar preguntas del quiz
QUIZ_FILE = Path(__file__).parent / "quiz.json"
QUIZ_QUESTIONS = []

def load_quiz_questions():
    """Carga las preguntas del quiz desde el archivo JSON"""
    global QUIZ_QUESTIONS
    try:
        with open(QUIZ_FILE, 'r', encoding='utf-8') as f:
            QUIZ_QUESTIONS = json.load(f)
        logger.info(f"✅ Cargadas {len(QUIZ_QUESTIONS)} preguntas del quiz")
    except FileNotFoundError:
        logger.error(f"❌ No se encontró el archivo {QUIZ_FILE}")
        QUIZ_QUESTIONS = []
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error al parsear JSON del quiz: {e}")
        QUIZ_QUESTIONS = []

# Cargar preguntas al importar el módulo
load_quiz_questions()

def get_random_questions(count: int = 5):
    """Obtiene preguntas aleatorias del quiz"""
    if len(QUIZ_QUESTIONS) < count:
        return QUIZ_QUESTIONS.copy()
    return random.sample(QUIZ_QUESTIONS, count)

def format_stars(score: int, total: int) -> str:
    """Formatea la puntuación con estrellas"""
    stars = "⭐" * score
    empty_stars = "☆" * (total - score)
    return f"{stars}{empty_stars}"

async def start_quiz_intro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pantalla de bienvenida del quiz"""
    query = update.callback_query
    
    # Intentar responder al query, pero ignorar si ya expiró
    try:
        await query.answer()
    except BadRequest as e:
        if "query is too old" in str(e).lower() or "query id is invalid" in str(e).lower():
            logger.warning(f"Callback query expirado, continuando sin responder: {e}")
        else:
            raise
    
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        try:
            await query.answer("❌ Error: No se pudo obtener el tenant ID.", show_alert=True)
        except BadRequest:
            pass  # Query ya expirado, no podemos responder
        return ConversationHandler.END
    
    # Verificar que el módulo quiz esté activo para este tenant
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            'SELECT admin_user_id FROM bots WHERE id = ?',
            (bot_id,)
        )
        result = await cursor.fetchone()
        if not result:
            try:
                await query.answer("❌ Error: No se encontró el doctor asociado.", show_alert=True)
            except BadRequest:
                pass
            return ConversationHandler.END
        
        doctor_telegram_id = result[0]
        doctor = await role_manager.get_doctor_by_telegram_id(doctor_telegram_id)
        if not doctor:
            try:
                await query.answer("❌ Error: No se encontró el doctor asociado.", show_alert=True)
            except BadRequest:
                pass
            return ConversationHandler.END
        
        doctor_id = doctor[0]
    
    is_active = await extra_modules_db.is_module_active_for_doctor(doctor_id, 'quiz')
    if not is_active:
        try:
            await query.answer("❌ El módulo Quiz no está disponible.", show_alert=True)
        except BadRequest:
            pass
        return ConversationHandler.END
    
    # Obtener nombre del usuario
    user = update.effective_user
    user_name = user.first_name or user.username or "Usuario"
    
    # Mensaje de bienvenida
    welcome_text = (
        f"👋 Hola <b>{escape_html(user_name)}</b>, soy <b>Ginekito</b> 🎮\n\n"
        f"¡Bienvenido/a a <b>Aprende Jugando</b>!\n\n"
        f"En este juego educativo podrás poner a prueba tus conocimientos sobre "
        f"mitos y verdades en salud ginecológica.\n\n"
        f"📋 <b>¿Cómo funciona?</b>\n"
        f"• Te haré <b>5 preguntas</b> aleatorias\n"
        f"• Responde si es <b>Mito</b> o <b>Verdad</b>\n"
        f"• Si te equivocas, te explicaré por qué\n"
        f"• Al final verás tu puntuación con estrellas ⭐\n\n"
        f"¡Vamos a aprender juntos! 🎓"
    )
    
    try:
        await query.edit_message_text(
            text=welcome_text,
            reply_markup=keyboards.get_start_quiz_keyboard(),
            parse_mode=ParseMode.HTML
        )
    except BadRequest as e:
        if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=welcome_text,
                reply_markup=keyboards.get_start_quiz_keyboard(),
                parse_mode=ParseMode.HTML
            )
        else:
            logger.warning(f"No se pudo editar el mensaje del quiz: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=welcome_text,
                reply_markup=keyboards.get_start_quiz_keyboard(),
                parse_mode=ParseMode.HTML
            )
    
    return WAITING_TO_START

async def start_quiz_game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia el juego del quiz (puede ser desde bienvenida o desde 'Jugar de nuevo')"""
    query = update.callback_query
    # Intentar responder al query, pero ignorar si ya expiró
    try:
        await query.answer()
    except BadRequest as e:
        if "query is too old" in str(e).lower() or "query id is invalid" in str(e).lower():
            logger.warning(f"Callback query expirado en start_quiz: {e}")
        else:
            raise
    
    # Obtener 5 preguntas aleatorias
    questions = get_random_questions(5)
    
    if not questions:
        try:
            await query.edit_message_text(
                "❌ Error: No se pudieron cargar las preguntas del quiz.",
                parse_mode=ParseMode.HTML
            )
        except BadRequest:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Error: No se pudieron cargar las preguntas del quiz.",
                parse_mode=ParseMode.HTML
            )
        return ConversationHandler.END
    
    # Limpiar datos anteriores y guardar nuevos
    context.user_data['quiz_questions'] = questions
    context.user_data['quiz_current_index'] = 0
    context.user_data['quiz_score'] = 0
    # Si viene de "Jugar de nuevo", usar el message_id del mensaje actual
    if query and query.message:
        context.user_data['quiz_message_id'] = query.message.message_id
    else:
        context.user_data['quiz_message_id'] = None
    
    # Mostrar primera pregunta
    await show_quiz_question(update, context)
    
    return PLAYING_QUIZ

async def show_quiz_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la pregunta actual del quiz"""
    user_data = context.user_data
    questions = user_data.get('quiz_questions', [])
    current_index = user_data.get('quiz_current_index', 0)
    
    if current_index >= len(questions):
        # Fin del juego
        await end_quiz(update, context)
        return
    
    question = questions[current_index]
    question_num = current_index + 1
    total_questions = len(questions)
    
    # Formatear pregunta
    question_text = (
        f"❓ <b>Mito o Verdad</b>\n\n"
        f"<b>Pregunta {question_num}/{total_questions}:</b>\n"
        f"<blockquote>{escape_html(question['statement'])}</blockquote>"
    )
    
    message_id = user_data.get('quiz_message_id')
    chat_id = update.effective_chat.id
    
    try:
        if message_id:
            # Editar mensaje existente
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=question_text,
                reply_markup=keyboards.get_quiz_question_keyboard(),
                parse_mode=ParseMode.HTML
            )
        else:
            # Enviar nuevo mensaje
            if update.callback_query:
                # Si hay un callback_query, intentar editar primero
                try:
                    msg = await update.callback_query.edit_message_text(
                        text=question_text,
                        reply_markup=keyboards.get_quiz_question_keyboard(),
                        parse_mode=ParseMode.HTML
                    )
                    user_data['quiz_message_id'] = msg.message_id
                except BadRequest:
                    # Si falla, enviar nuevo mensaje
                    msg = await context.bot.send_message(
                        chat_id=chat_id,
                        text=question_text,
                        reply_markup=keyboards.get_quiz_question_keyboard(),
                        parse_mode=ParseMode.HTML
                    )
                    user_data['quiz_message_id'] = msg.message_id
            else:
                msg = await context.bot.send_message(
                    chat_id=chat_id,
                    text=question_text,
                    reply_markup=keyboards.get_quiz_question_keyboard(),
                    parse_mode=ParseMode.HTML
                )
                user_data['quiz_message_id'] = msg.message_id
    except BadRequest as e:
        logger.warning(f"Error al mostrar pregunta del quiz: {e}")
        # Enviar nuevo mensaje como fallback
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=question_text,
            reply_markup=keyboards.get_quiz_question_keyboard(),
            parse_mode=ParseMode.HTML
        )
        user_data['quiz_message_id'] = msg.message_id

async def handle_quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la respuesta del usuario"""
    query = update.callback_query
    # Intentar responder al query, pero ignorar si ya expiró
    try:
        await query.answer()
    except BadRequest as e:
        if "query is too old" in str(e).lower() or "query id is invalid" in str(e).lower():
            logger.warning(f"Callback query expirado en handle_answer: {e}")
        else:
            raise
    
    user_data = context.user_data
    questions = user_data.get('quiz_questions', [])
    current_index = user_data.get('quiz_current_index', 0)
    
    if current_index >= len(questions):
        return ConversationHandler.END
    
    question = questions[current_index]
    user_answer = query.data == "quiz_answer_true"  # True si presionó "Verdad"
    correct_answer = question['is_truth']
    
    is_correct = user_answer == correct_answer
    
    # Actualizar puntuación
    if is_correct:
        user_data['quiz_score'] = user_data.get('quiz_score', 0) + 1
    
    message_id = user_data.get('quiz_message_id')
    chat_id = update.effective_chat.id
    
    # Mostrar resultado
    if is_correct:
        answer_type = 'Verdad' if correct_answer else 'Mito'
        result_text = (
            f"✅ <b>¡Es Correcto!</b> Es <b>{answer_type}</b>\n\n"
            f"<blockquote>{escape_html(question['statement'])}</blockquote>"
        )
        # Si es correcto, mostrar el resultado con los mismos botones (estáticos)
        # y avanzar automáticamente después de un breve delay
        try:
            if message_id:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=result_text,
                    reply_markup=keyboards.get_quiz_question_keyboard(),
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.edit_message_text(
                    text=result_text,
                    reply_markup=keyboards.get_quiz_question_keyboard(),
                    parse_mode=ParseMode.HTML
                )
                user_data['quiz_message_id'] = query.message.message_id
        except BadRequest:
            msg = await context.bot.send_message(
                chat_id=chat_id,
                text=result_text,
                reply_markup=keyboards.get_quiz_question_keyboard(),
                parse_mode=ParseMode.HTML
            )
            user_data['quiz_message_id'] = msg.message_id
        
        # Esperar un momento antes de avanzar
        import asyncio
        await asyncio.sleep(1.5)
        
        # Avanzar índice
        user_data['quiz_current_index'] = current_index + 1
        
        # Mostrar siguiente pregunta o finalizar
        if user_data['quiz_current_index'] < len(questions):
            await show_quiz_question(update, context)
        else:
            await end_quiz(update, context)
        
        return PLAYING_QUIZ
    else:
        # Si es incorrecto, mostrar explicación con botón "Entendido"
        result_text = (
            f"❌ <b>Incorrecto</b>\n\n"
            f"<blockquote>{escape_html(question['statement'])}</blockquote>\n\n"
            f"<b>Explicación:</b>\n"
            f"{escape_html(question['explanation'])}"
        )
        
        try:
            if message_id:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=result_text,
                    reply_markup=keyboards.get_quiz_explanation_keyboard(),
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.edit_message_text(
                    text=result_text,
                    reply_markup=keyboards.get_quiz_explanation_keyboard(),
                    parse_mode=ParseMode.HTML
                )
                user_data['quiz_message_id'] = query.message.message_id
        except BadRequest:
            msg = await context.bot.send_message(
                chat_id=chat_id,
                text=result_text,
                reply_markup=keyboards.get_quiz_explanation_keyboard(),
                parse_mode=ParseMode.HTML
            )
            user_data['quiz_message_id'] = msg.message_id
        
        # Cambiar a estado de explicación
        return SHOWING_EXPLANATION

async def handle_quiz_understood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja cuando el usuario presiona 'Entendido' después de ver la explicación"""
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest as e:
        if "query is too old" in str(e).lower() or "query id is invalid" in str(e).lower():
            logger.warning(f"Callback query expirado en handle_understood: {e}")
        else:
            raise
    
    user_data = context.user_data
    questions = user_data.get('quiz_questions', [])
    current_index = user_data.get('quiz_current_index', 0)
    
    # Avanzar índice
    user_data['quiz_current_index'] = current_index + 1
    
    # Mostrar siguiente pregunta o finalizar
    if user_data['quiz_current_index'] < len(questions):
        await show_quiz_question(update, context)
    else:
        await end_quiz(update, context)
    
    return PLAYING_QUIZ

async def end_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finaliza el quiz y muestra la puntuación"""
    user_data = context.user_data
    score = user_data.get('quiz_score', 0)
    total = len(user_data.get('quiz_questions', []))
    
    if total == 0:
        total = 5  # Fallback
    
    # Formatear estrellas
    stars = format_stars(score, total)
    
    final_text = (
        f"🎉 <b>¡Juego Completado!</b>\n\n"
        f"<b>Puntuación:</b> {stars}\n"
        f"<b>Resultado:</b> {score}/{total} correctas\n\n"
    )
    
    if score == total:
        final_text += "🌟 ¡Perfecto! Respondiste todas correctamente. ¡Eres un/a experto/a! 🌟"
    elif score >= total * 0.8:
        final_text += "👏 ¡Excelente! Tienes muy buenos conocimientos."
    elif score >= total * 0.6:
        final_text += "👍 ¡Bien hecho! Sigue aprendiendo."
    else:
        final_text += "📚 ¡Sigue practicando! Cada pregunta es una oportunidad de aprender."
    
    message_id = user_data.get('quiz_message_id')
    chat_id = update.effective_chat.id
    
    try:
        if message_id:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=final_text,
                reply_markup=keyboards.get_quiz_final_keyboard(),
                parse_mode=ParseMode.HTML
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=final_text,
                reply_markup=keyboards.get_quiz_final_keyboard(),
                parse_mode=ParseMode.HTML
            )
    except BadRequest:
        await context.bot.send_message(
            chat_id=chat_id,
            text=final_text,
            reply_markup=keyboards.get_quiz_final_keyboard(),
            parse_mode=ParseMode.HTML
        )
    
    # Limpiar datos del quiz
    user_data.pop('quiz_questions', None)
    user_data.pop('quiz_current_index', None)
    user_data.pop('quiz_score', None)
    user_data.pop('quiz_message_id', None)

async def cancel_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela el quiz"""
    query = update.callback_query
    # Intentar responder al query, pero ignorar si ya expiró
    try:
        await query.answer("Juego cancelado")
    except BadRequest as e:
        if "query is too old" in str(e).lower() or "query id is invalid" in str(e).lower():
            logger.warning(f"Callback query expirado en cancel_quiz: {e}")
        else:
            raise
    
    # Limpiar datos
    context.user_data.pop('quiz_questions', None)
    context.user_data.pop('quiz_current_index', None)
    context.user_data.pop('quiz_score', None)
    context.user_data.pop('quiz_message_id', None)
    
    # Mostrar mensaje de cancelación
    try:
        await query.edit_message_text(
            "❌ <b>Juego cancelado</b>\n\nVolviendo al menú principal...",
            parse_mode=ParseMode.HTML
        )
        # Esperar un momento antes de redirigir
        import asyncio
        await asyncio.sleep(1)
    except BadRequest:
        pass
    
    # Redirigir al menú principal según el rol del usuario
    user_id = update.effective_user.id
    user_role = await role_manager.get_user_role(user_id)
    
    # Obtener el mensaje que se va a editar
    message_to_edit = query.message if query else update.effective_message
    chat_id = update.effective_chat.id
    
    # Editar el mensaje directamente con el contenido del menú según el rol
    try:
        if user_role == 'superadmin':
            from features.marketing.handler import send_marketing_menu
            # Eliminar el mensaje de cancelación y enviar el menú de marketing
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_to_edit.message_id)
            except:
                pass
            await send_marketing_menu(update, context, is_superadmin=True)
        elif user_role == 'doctor':
            from features.main_menu.user_handler import get_doctor_public_keyboard
            doctor = await role_manager.get_doctor_by_telegram_id(user_id)
            doctor_name = doctor[1] if doctor else "Tu perfil"
            message = (
                f"👩‍⚕️ <b>Menú Principal - {doctor_name}</b>\n"
                "Comparte estos accesos con tus pacientes y personalízalos desde Panel Admin."
            )
            keyboard = await get_doctor_public_keyboard(user_id=user_id)
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_to_edit.message_id,
                text=message,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        elif user_role == 'patient':
            from features.patient_menu.patient_keyboards import get_patient_main_keyboard
            doctor = await role_manager.get_assigned_doctor(user_id)
            if doctor:
                doctor_id = doctor[0]
                doctor = await role_manager.get_doctor_by_id(doctor_id)
                doctor_name = doctor[1] if doctor else "tu doctora"
                message = (
                    f"👤 <b>Menú Principal - {doctor_name}</b>\n"
                    
                )
                keyboard = await get_patient_main_keyboard(doctor_id=doctor_id)
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_to_edit.message_id,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                from features.marketing.handler import send_marketing_menu
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=message_to_edit.message_id)
                except:
                    pass
                await send_marketing_menu(update, context)
        else:
            from features.marketing.handler import send_marketing_menu
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_to_edit.message_id)
            except:
                pass
            await send_marketing_menu(update, context)
    except Exception as e:
        logger.error(f"Error al redirigir al menú principal después de cancelar quiz: {e}")
        # Fallback: enviar mensaje de error
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Error al volver al menú principal. Por favor, usa /start"
            )
        except:
            pass
    
    return ConversationHandler.END

def register(app: Application):
    """Registra los handlers del módulo quiz"""
    quiz_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_quiz_intro, pattern='^quiz_start_intro$'),
            CallbackQueryHandler(start_quiz_game, pattern='^quiz_start_game$')
        ],
        states={
            WAITING_TO_START: [
                CallbackQueryHandler(start_quiz_game, pattern='^quiz_start_game$'),
                CallbackQueryHandler(cancel_quiz, pattern='^quiz_cancel$')
            ],
            PLAYING_QUIZ: [
                CallbackQueryHandler(handle_quiz_answer, pattern='^quiz_answer_(true|false)$'),
                CallbackQueryHandler(cancel_quiz, pattern='^quiz_cancel$')
            ],
            SHOWING_EXPLANATION: [
                CallbackQueryHandler(handle_quiz_understood, pattern='^quiz_understood$'),
                CallbackQueryHandler(cancel_quiz, pattern='^quiz_cancel$')
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_quiz, pattern='^quiz_cancel$'),
            CallbackQueryHandler(handle_all_callbacks, pattern='^main_menu$')
        ],
        per_message=False,
        allow_reentry=True
    )
    app.add_handler(quiz_conv)

