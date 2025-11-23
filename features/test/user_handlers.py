# /features/test/user_handlers.py
import logging
import time
from database import user_db, content_db
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, ConversationHandler, CallbackQueryHandler, ContextTypes
)

from common import texts as common_texts
from . import keyboards
from common.helpers import generate_progress_bar
from common.context_manager import get_tenant_id
from database import extra_modules_db
from utils.role_manager import RoleManager
from config import DB_PATH
from handlers.callback_router import handle_all_callbacks

from telegram.constants import ParseMode
from common.helpers import escape_html

logger = logging.getLogger(__name__)
role_manager = RoleManager(DB_PATH)

TEXTO_INICIO_TEST = (
    "📋 Este test es una <b>guía orientativa</b> y no reemplaza una evaluación médica.\n\n"
    "<b>Instrucciones:</b>\n"
    "Responde a cada pregunta. Tu puntuación final indicará un nivel de coincidencia con síntomas comunes."
)

(ASKING_QUESTION,) = range(1)

async def start_test_intro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await query.answer("❌ Error: No se pudo obtener el tenant ID.", show_alert=True)
        return ConversationHandler.END
    
    # Verificar que el módulo test esté activo para este tenant
    # Obtener doctor_id desde bot_id
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute(
            'SELECT admin_user_id FROM bots WHERE id = ?',
            (bot_id,)
        )
        result = await cursor.fetchone()
        if not result:
            await query.answer("❌ Error: No se encontró el doctor asociado.", show_alert=True)
            return ConversationHandler.END
        
        doctor_telegram_id = result[0]
        doctor = await role_manager.get_doctor_by_telegram_id(doctor_telegram_id)
        if not doctor:
            await query.answer("❌ Error: No se encontró el doctor asociado.", show_alert=True)
            return ConversationHandler.END
        
        doctor_id = doctor[0]
    is_active = await extra_modules_db.is_module_active_for_doctor(doctor_id, 'test')
    if not is_active:
        await query.answer("❌ El módulo Test no está disponible.", show_alert=True)
        return ConversationHandler.END
    
    user_id = update.effective_user.id

    if await user_db.has_user_completed_action(user_id, bot_id, 'completed_endo_test'):
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Menú Principal", callback_data="main_menu")]
        ])
        await query.edit_message_text(
            text="✅ Ya has completado este test. Solo se permite realizarlo una vez.",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
        return ConversationHandler.END

    await query.edit_message_text(
        text=TEXTO_INICIO_TEST,
        reply_markup=keyboards.get_start_test_keyboard(),
        parse_mode="HTML"
    )
    return ASKING_QUESTION

async def start_test_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await query.answer("❌ Error: No se pudo obtener el tenant ID.", show_alert=True)
        return ConversationHandler.END

    question_items = await content_db.get_all_items(bot_id, 'test_questions', 'question')
    questions = [item['title'] for item in question_items]

    if not questions:
        await query.edit_message_text(
            "Lo siento, las preguntas para el test no están configuradas.",
            parse_mode="HTML"
        )
        return ConversationHandler.END

    context.user_data.update({
        'test_questions': questions,
        'test_score': 0,
        'test_question_index': 0,
        'test_answers': [],
        'test_message_id': None
    })

    await query.delete_message()
    return await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    q_idx = user_data['test_question_index']
    questions = user_data['test_questions']

    message_text = (f"<b>{q_idx + 1}/{len(questions)}</b>: {questions[q_idx]}\n\n"
                    f"{generate_progress_bar(user_data['test_answers'], len(questions))}")

    reply_markup = keyboards.get_test_question_keyboard()
    message_id = user_data.get('test_message_id')
    chat_id = update.effective_chat.id

    if message_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=message_id,
                text=message_text, reply_markup=reply_markup,
                parse_mode="HTML"
            )
        except Exception:
            message = await context.bot.send_message(
                chat_id=chat_id, text=message_text,
                reply_markup=reply_markup, parse_mode="HTML"
            )
            user_data['test_message_id'] = message.message_id
    else:
        message = await context.bot.send_message(
            chat_id=chat_id, text=message_text,
            reply_markup=reply_markup, parse_mode="HTML"
        )
        user_data['test_message_id'] = message.message_id

    return ASKING_QUESTION

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    user_data = context.user_data
    if query.data == 'test_answer_yes':
        user_data['test_answers'].append('yes'); user_data['test_score'] += 1
    else:
        user_data['test_answers'].append('no')
    user_data['test_question_index'] += 1
    if user_data['test_question_index'] < len(user_data['test_questions']):
        return await ask_question(update, context)
    else:
        return await end_test(update, context)

async def end_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        # Si no hay query, crear un mensaje de error
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.answer("❌ Error: No se pudo obtener el tenant ID.", show_alert=True)
        return ConversationHandler.END
    
    user_id = update.effective_user.id

    # Registramos que el test fue completado
    await user_db.log_user_action(
        user_id=user_id,
        bot_id=bot_id,
        action_key='completed_endo_test',
        timestamp=int(time.time())
    )

    resultado_texto = common_texts.get_resultado_test(score=user_data['test_score'], total_questions=len(user_data['test_questions']))

    # --- ¡LÓGICA DE NOTIFICACIÓN MODIFICADA! ---
    try:
        # Obtener doctor desde bot_id
        # bot_id está en la tabla bots, que tiene admin_user_id (telegram_id del doctor)
        import aiosqlite
        async with aiosqlite.connect(DB_PATH) as conn:
            cursor = await conn.execute(
                'SELECT admin_user_id FROM bots WHERE id = ?',
                (bot_id,)
            )
            result = await cursor.fetchone()
            if result:
                doctor_telegram_id = result[0]
                doctor = await role_manager.get_doctor_by_telegram_id(doctor_telegram_id)
                if doctor:
                    doctor_id = doctor[0]
                    user = update.effective_user
                    user_info = user.full_name
                    if user.username:
                        user_info += f" (@{user.username})"

                    notification_text = (
                        f"🔔 Nuevo test completado\n\n"
                        f"👤 <b>Usuario:</b> {escape_html(user_info)}\n\n"
                        f"📝 <b>Resultado:</b>\n"
                        f"<blockquote>{resultado_texto}</blockquote>"
                    )

                    # Creamos el teclado con el botón para descartar
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🗑️ Descartar Notificación", callback_data="dismiss_test_notification")]
                    ])

                    await context.bot.send_message(
                        chat_id=doctor_telegram_id,
                        text=notification_text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard
                    )
                    logger.info(f"Notificación de test completado enviada al doctor {doctor_telegram_id} para el usuario {user.id}.")
                else:
                    logger.warning(f"No se encontró un doctor con telegram_id {doctor_telegram_id} para el bot_id {bot_id}.")
            else:
                logger.warning(f"No se encontró un bot_id {bot_id} en la tabla bots. No se pudo enviar la notificación del test.")
    except Exception as e:
        logger.error(f"FALLO al enviar notificación de test al admin: {e}", exc_info=True)
    # --- FIN DE LA MODIFICACIÓN ---

    # Mostramos el resultado al usuario (sin cambios)
    final_message = (f"{generate_progress_bar(user_data['test_answers'], len(user_data['test_questions']))}\n\n{resultado_texto}")
    if 'test_message_id' in user_data:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id, message_id=user_data['test_message_id'],
            text=final_message, reply_markup=keyboards.get_return_to_main_menu_keyboard(),
            parse_mode="HTML"
        )

    user_data.clear()
    return ConversationHandler.END


async def cancel_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela el test. NO registra nada. Solo limpia y vuelve al menú."""
    query = update.callback_query
    await query.answer("Test cancelado.")
    context.user_data.clear()
    # Usar el router centralizado en lugar de show_main_menu para evitar imports circulares
    await handle_all_callbacks(update, context)
    return ConversationHandler.END

async def dismiss_test_notification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador para el botón 'Descartar Notificación'. Simplemente borra el mensaje."""
    query = update.callback_query
    await query.answer()
    try:
        await query.message.delete()
    except Exception as e:
        logger.warning(f"No se pudo borrar el mensaje de notificación: {e}")

def register(app: Application):
    test_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_test_intro, pattern='^start_endo_test$')],
        states={
            ASKING_QUESTION: [
                CallbackQueryHandler(start_test_questions, pattern='^begin_test$'),
                # --- ¡CORRECCIÓN AQUÍ! ---
                # Añadimos la coma que faltaba al final de esta línea.
                CallbackQueryHandler(handle_answer, pattern='^test_answer_(yes|no)$'),
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_test, pattern='^cancel_test$'),

            CallbackQueryHandler(handle_all_callbacks, pattern='^main_menu$')
        ],
        per_message=False,
        allow_reentry=True
    )
    app.add_handler(test_conv)
    app.add_handler(CallbackQueryHandler(dismiss_test_notification, pattern='^dismiss_test_notification$'))