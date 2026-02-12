# /features/test/user_handlers.py
import logging
import time
from database import user_db, content_db
from database.session import get_session
from database.models.bot import Bot
from database.models.user import Doctor
from sqlalchemy import select
from common import texts
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
from database.repositories.test_result_repository import TestResultRepository
from database.repositories.user_util_repository import BotRepository

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

async def _get_bot_id_for_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    """
    Obtiene el bot_id para el test, priorizando el doctor con el que interactúa el paciente.
    Similar a cómo funciona en el módulo de citas.
    """
    user_id = update.effective_user.id
    logger.info(f"[_get_bot_id_for_test] Usuario {user_id}: Iniciando búsqueda de bot_id")
    
    # 1. Si el usuario es doctor, usar su propio bot_id
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    if doctor:
        doctor_telegram_id = doctor[2]  # telegram_id está en índice 2
        logger.info(f"[_get_bot_id_for_test] Usuario {user_id}: Es doctor, telegram_id={doctor_telegram_id}")
        async with get_session() as session:
            stmt = select(Bot.id).where(Bot.admin_user_id == doctor_telegram_id)
            result = await session.execute(stmt)
            bot_id = result.scalar_one_or_none()
            if bot_id:
                logger.info(f"[_get_bot_id_for_test] Usuario {user_id}: Bot ID encontrado para doctor: {bot_id}")
                return bot_id
            else:
                logger.warning(f"[_get_bot_id_for_test] Usuario {user_id}: No se encontró bot_id para doctor telegram_id={doctor_telegram_id}")
    
    # 2. Si es paciente, buscar el doctor asignado
    doctor_id = context.user_data.get("patient_doctor_id")
    logger.info(f"[_get_bot_id_for_test] Usuario {user_id}: patient_doctor_id en context = {doctor_id}")
    
    if not doctor_id:
        assigned_doctor = await role_manager.get_assigned_doctor(user_id)
        if assigned_doctor:
            doctor_id = assigned_doctor[0]
            logger.info(f"[_get_bot_id_for_test] Usuario {user_id}: Doctor asignado encontrado: {doctor_id}")
    
    if doctor_id:
        # Obtener bot_id desde doctor_id
        async with get_session() as session:
            # Buscar bot por admin_user_id del doctor
            stmt_doctor = select(Doctor).where(Doctor.id == doctor_id)
            result_doctor = await session.execute(stmt_doctor)
            doctor_obj = result_doctor.scalar_one_or_none()
            if doctor_obj:
                logger.info(f"[_get_bot_id_for_test] Usuario {user_id}: Doctor objeto encontrado, telegram_id={doctor_obj.telegram_id}")
                stmt_bot = select(Bot.id).where(Bot.admin_user_id == doctor_obj.telegram_id)
                result_bot = await session.execute(stmt_bot)
                bot_id = result_bot.scalar_one_or_none()
                if bot_id:
                    logger.info(f"[_get_bot_id_for_test] Usuario {user_id}: Bot ID encontrado para paciente: {bot_id}")
                    return bot_id
                else:
                    logger.warning(f"[_get_bot_id_for_test] Usuario {user_id}: No se encontró bot_id para doctor_id={doctor_id}")
    
    # 3. Fallback: usar get_tenant_id (para SuperAdmin o usuarios sin doctor asignado)
    fallback_bot_id = await get_tenant_id(update, context)
    logger.info(f"[_get_bot_id_for_test] Usuario {user_id}: Usando fallback get_tenant_id: {fallback_bot_id}")
    return fallback_bot_id

async def start_test_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    bot_id = await _get_bot_id_for_test(update, context)
    logger.info(f"[start_test_questions] Usuario {user_id}: bot_id obtenido = {bot_id}")
    
    if not bot_id:
        logger.error(f"[start_test_questions] Usuario {user_id}: No se pudo obtener bot_id")
        await query.answer("❌ Error: No se pudo obtener el tenant ID.", show_alert=True)
        return ConversationHandler.END

    logger.info(f"[start_test_questions] Usuario {user_id}: Consultando preguntas para bot_id={bot_id}")
    question_items = await content_db.get_all_items(bot_id, 'test_questions', 'question')
    questions = [item['title'] for item in question_items]
    logger.info(f"[start_test_questions] Usuario {user_id}: Se encontraron {len(questions)} preguntas para bot_id={bot_id}")

    if not questions:
        logger.warning(f"[start_test_questions] Usuario {user_id}: No se encontraron preguntas para bot_id={bot_id}")
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
    query = update.callback_query
    await query.answer()
    
    logger.info(f"[handle_answer] Callback recibido: {query.data}")
    
    user_data = context.user_data
    if query.data == 'test_answer_yes':
        user_data['test_answers'].append('yes')
        user_data['test_score'] += 1
        logger.info(f"[handle_answer] Respuesta: Sí, score actual: {user_data['test_score']}")
    elif query.data == 'test_answer_no':
        user_data['test_answers'].append('no')
        logger.info(f"[handle_answer] Respuesta: No, score actual: {user_data['test_score']}")
    else:
        logger.warning(f"[handle_answer] Callback desconocido: {query.data}")
        return ASKING_QUESTION
    
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
        # Calcular el nivel de resultado para guardar en BD (replicando lógica de common/texts.py)
        # Esto permite estadísticas agrupadas
        score = user_data['test_score']
        total_q = len(user_data['test_questions'])
        percent = (score / total_q) * 100 if total_q > 0 else 0
        
        if percent >= 70:
            result_level = "ALTA COINCIDENCIA"
        elif percent >= 40:
            result_level = "MODERADA COINCIDENCIA"
        else:
            result_level = "BAJA COINCIDENCIA"

        # Guardar resultado y obtener estadísticas
        async with get_session() as session:
            test_repo = TestResultRepository(session)
            bot_repo = BotRepository(session)
            
            # Guardamos el resultado detallado
            await test_repo.save_result(
                user_id=user_id,
                bot_id=bot_id,
                score=score,
                total_questions=total_q,
                result_level=result_level,
                timestamp=int(time.time())
            )
            
            # Obtenemos estadísticas actualizadas y completas
            total_tests = await test_repo.get_total_tests_count(bot_id)
            distribution = await test_repo.get_result_distribution(bot_id)
            
            # Helper para calcular porcentaje seguro
            def calc_pct(count, total):
                return (count / total * 100) if total > 0 else 0
            
            pct_high = calc_pct(distribution['ALTA COINCIDENCIA'], total_tests)
            pct_med = calc_pct(distribution['MODERADA COINCIDENCIA'], total_tests)
            pct_low = calc_pct(distribution['BAJA COINCIDENCIA'], total_tests)
            
            # Fecha actual formateada
            from datetime import datetime
            import pytz
            # Usar zona horaria si es posible, o UTC/Local
            date_str = datetime.now().strftime("%d/%m/%Y")

            # Obtener doctor para notificar
            doctor_telegram_id = await bot_repo.get_bot_admin_id(bot_id)
            
            if doctor_telegram_id:
                doctor_tuple = await role_manager.get_doctor_by_telegram_id(doctor_telegram_id)
                if doctor_tuple:
                    user = update.effective_user
                    user_info = user.full_name
                    if user.username:
                        user_info += f" (@{user.username})"

                    notification_text = (
                        f"🔔 <b>Nuevo test completado</b>\n"
                        f"#{result_level.replace(' ', '')}\n\n"
                        f"👤 <b>Usuario:</b> {escape_html(user_info)}\n\n"
                        f"📝 <b>Resultado:</b>\n"
                        f"<blockquote>{resultado_texto}</blockquote>\n\n"
                        f"📊 <b>Estadísticas Globales</b>\n"
                        f"<i>(Total de tests: {total_tests} al {date_str})</i>\n\n"
                        f"🔴 <b>{pct_high:.0f}%</b> Alta coincidencia\n"
                        f"🟡 <b>{pct_med:.0f}%</b> Media coincidencia\n"
                        f"🟢 <b>{pct_low:.0f}%</b> Baja coincidencia"
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
                    logger.info(f"Notificación enriquecida enviada al doctor {doctor_telegram_id}.")
                else:
                    logger.warning(f"No se encontró doctor tuple para {doctor_telegram_id}")
            else:
                logger.warning(f"No se encontró admin_id para bot {bot_id}")

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
    
    logger.info(f"[cancel_test] Test cancelado por usuario {update.effective_user.id}")
    
    # Limpiar datos del test
    context.user_data.clear()
    
    # Redirigir al menú principal según el rol del usuario
    # IMPORTANTE: Enviar nuevo mensaje en lugar de editar, porque el mensaje del test puede haber sido eliminado
    try:
        from features.main_menu.user_handler import get_doctor_public_keyboard, admin_main_menu
        from features.patient_menu.patient_handler import patient_main_menu
        from utils.role_manager import RoleManager
        from config import DB_PATH
        
        role_mgr = RoleManager(DB_PATH)
        user_id = update.effective_user.id
        user_role = await role_mgr.get_user_role(user_id)
        
        logger.info(f"[cancel_test] Redirigiendo usuario {user_id} (rol: {user_role}) al menú principal")
        
        if user_role == 'doctor':
            # Para doctores, construir el mensaje completo como en admin_main_menu
            # Obtener doctor y bot_id para el mensaje
            doctor = await role_mgr.get_doctor_by_telegram_id(user_id)
            doctor_name = doctor[1] if doctor else "Doctor"
            
            bot_id = None
            if doctor:
                from database.session import get_session
                from database.models.bot import Bot
                from sqlalchemy import select
                async with get_session() as session:
                    stmt = select(Bot.id).where(Bot.admin_user_id == doctor[2])
                    result = await session.execute(stmt)
                    bot_id = result.scalar_one_or_none()
            
            if not bot_id:
                bot_id = 1
            
            # Obtener mensaje de bienvenida
            from common import texts
            user_name = update.effective_user.first_name or "Usuario"
            mensaje_bienvenida = await texts.get_mensaje_bienvenida(nombre_usuario=user_name, bot_id=bot_id)
            
            # Construir mensaje final (igual que admin_main_menu)
            message = f" {mensaje_bienvenida}"
            
            # Obtener teclado con módulos activos (igual que admin_main_menu)
            # get_doctor_public_keyboard ya verifica los módulos activos internamente
            keyboard = await get_doctor_public_keyboard(user_id)
            
            try:
                # Intentar editar primero
                await query.edit_message_text(
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"[cancel_test] No se pudo editar mensaje: {e}, enviando nuevo mensaje")
                # Si falla, enviar nuevo mensaje
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                
        elif user_role == 'patient':
            doctor = await role_mgr.get_assigned_doctor(user_id)
            if doctor:
                # Para pacientes, usar patient_main_menu que maneja el envío de nuevo mensaje
                await patient_main_menu(update, context, doctor[0])
            else:
                # Si no tiene doctor, enviar mensaje simple
                try:
                    await query.edit_message_text(
                        text="✅ Test cancelado. Usa /start para comenzar.",
                        parse_mode="HTML"
                    )
                except Exception:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="✅ Test cancelado. Usa /start para comenzar.",
                        parse_mode="HTML"
                    )
        else:
            # Para otros roles, enviar mensaje simple
            try:
                await query.edit_message_text(
                    text="✅ Test cancelado. Usa /start para comenzar.",
                    parse_mode="HTML"
                )
            except Exception:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="✅ Test cancelado. Usa /start para comenzar.",
                    parse_mode="HTML"
                )
        
        logger.info(f"[cancel_test] Redirección completada")
        
    except Exception as e:
        logger.error(f"[cancel_test] Error al redirigir al menú: {e}", exc_info=True)
        # Fallback: enviar mensaje simple
        try:
            await query.edit_message_text(
                text="✅ Test cancelado. Usa /start para comenzar.",
                parse_mode="HTML"
            )
        except Exception:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="✅ Test cancelado. Usa /start para comenzar.",
                    parse_mode="HTML"
                )
            except Exception as e2:
                logger.error(f"[cancel_test] Error enviando mensaje de fallback: {e2}")
    
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
                # Usar un solo handler con regex para ambas respuestas (como en el bot viejo)
                CallbackQueryHandler(handle_answer, pattern='^test_answer_(yes|no)$'),
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_test, pattern='^cancel_test$'),
            CallbackQueryHandler(handle_all_callbacks, pattern='^main_menu$')
        ],
        per_message=False,  # Cambiar a False como en el bot viejo
        allow_reentry=True
    )
    app.add_handler(test_conv)
    app.add_handler(CallbackQueryHandler(dismiss_test_notification, pattern='^dismiss_test_notification$'))