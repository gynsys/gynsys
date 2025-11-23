# features/citas/admin_handlers.py
import logging
import asyncio
import html
from datetime import date, datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, CallbackQueryHandler, Application
)
from telegram.ext import CommandHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

from config import DB_PATH
from database.session import get_session
from database.repositories.appointment_repository import SlotRepository, AppointmentRepository
from utils.role_manager import RoleManager
from . import admin_keyboards as keyboards
from .admin_calendar import CustomCalendar
from . import user_keyboards
from features.main_menu.user_handler import admin_main_menu

logger = logging.getLogger(__name__)
CITAS_PER_PAGE = 5

role_manager = RoleManager(DB_PATH)

# Helper para escape_html
def escape_html(text: str) -> str:
    return html.escape(str(text))

# Helper para obtener doctor_id
async def _get_doctor_id(update: Update) -> int:
    """Obtiene el doctor_id del usuario actual."""
    user_id = update.effective_user.id
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    return doctor[0] if doctor else None

def _build_proxy_update(original_query, data: str, update: Update):
    """Crea un proxy de CallbackQuery para reutilizar handlers existentes."""
    class ProxyQuery:
        def __init__(self, original, data):
            self._original = original
            self.data = data
            self.message = original.message

        async def answer(self, *args, **kwargs):
            return await self._original.answer(*args, **kwargs)

        async def edit_message_text(self, *args, **kwargs):
            return await self._original.edit_message_text(*args, **kwargs)

        async def edit_message_reply_markup(self, *args, **kwargs):
            return await self._original.edit_message_reply_markup(*args, **kwargs)

    class ProxyUpdate:
        def __init__(self, proxy_query, user, chat):
            self.callback_query = proxy_query
            self.effective_user = user
            self.effective_chat = chat

    proxy_query = ProxyQuery(original_query, data)
    return ProxyUpdate(proxy_query, update.effective_user, update.effective_chat)

async def _redirect_to_list(query, update, context, filter_type, page_index):
    proxy_update = _build_proxy_update(query, f"citas_view_{filter_type}_{page_index}", update)
    await list_and_detail_handler(proxy_update, context)

async def _redirect_to_detail(query, update, context, cita_id, filter_type, page_index):
    proxy_update = _build_proxy_update(query, f"citas_detail_{cita_id}_{filter_type}_{page_index}", update)
    await list_and_detail_handler(proxy_update, context)

# Función para redirigir al menú de citas del doctor (va directamente a la lista)
async def doctor_citas_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Redirige directamente a la lista de citas usando un callback proxy."""
    original_query = update.callback_query
    if not original_query:
        return

    await original_query.answer()

    proxy_update = _build_proxy_update(original_query, "citas_view_all-pending_0", update)
    await list_and_detail_handler(proxy_update, context)


# TODO: Adaptar funciones restantes para multi-tenant
# Las siguientes funciones están comentadas temporalmente hasta adaptarlas completamente
"""
# @admin_required  # TODO: Adaptar para multi-tenant
async def force_reminders_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Comentado temporalmente - necesita adaptación
    pass
"""



# Funciones adaptadas para multi-tenant
async def list_and_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la lista y el detalle de citas del doctor."""
    query = update.callback_query
    if not query:
        return
    await query.answer()

    logger.info(f"[citas] callback recibido: {query.data}")

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text(
            "⚠️ Solo los médicos activos pueden gestionar citas.",
            parse_mode="HTML"
        )
        return

    parts = query.data.split('_')
    view_type = parts[1] if len(parts) > 1 else 'view'

    if view_type == 'view':
        filter_type = parts[2] if len(parts) > 2 else 'all-pending'
        page_index = int(parts[3]) if len(parts) > 3 else 0
        status_map = {
            "pending": ["pending"],
            "confirmed": ["confirmed"],
            "completed": ["completed"],
        }
        statuses = status_map.get(filter_type, None)
        async with get_session() as session:
            appointment_repo = AppointmentRepository(session)
            appointments = await appointment_repo.get_appointments_for_doctor(doctor_id, statuses)
        logger.debug(f"[citas] list view -> filtro={filter_type} pag={page_index} total={len(appointments)}")

        citas_formatted = []
        for apt in appointments:
            dt = datetime.fromtimestamp(apt["start_ts"])
            citas_formatted.append(
                {
                    "id": apt["id"],
                    "fecha": dt.strftime("%d/%m/%Y"),
                    "hora": dt.strftime("%H:%M"),
                    "user_name": escape_html(apt["patient_name"] or f"Paciente {apt['patient_telegram_id']}"),
                    "motivo": escape_html(apt["reason"] or ""),
                    "ubicacion": escape_html(apt["location"] or ""),
                }
            )

        start_index = page_index * CITAS_PER_PAGE
        citas_paginadas = citas_formatted[start_index : start_index + CITAS_PER_PAGE]
        total_citas = len(citas_formatted)

        if not citas_formatted:
            text = "👍 No hay citas que coincidan con este filtro."
        else:
            total_paginas = max(1, (total_citas + CITAS_PER_PAGE - 1) // CITAS_PER_PAGE)
            text = f"<b>📅 Citas Encontradas</b> (Página {page_index + 1}/{total_paginas})"

        # Enriquecer la descripción mostrada en la lista
        for cita in citas_paginadas:
            descripcion = f"{cita['fecha']} {cita['hora']} - {cita['user_name']}"
            if cita["motivo"]:
                descripcion += f" ({cita['motivo']})"
            cita["descripcion"] = descripcion

        reply_markup = keyboards.get_citas_list_keyboard(citas_paginadas, page_index, total_citas, filter_type)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
        return True

    elif view_type == 'detail':
        cita_id = int(parts[2]) if len(parts) > 2 else 0
        filter_type = parts[3] if len(parts) > 3 else "all-pending"
        page_index = int(parts[4]) if len(parts) > 4 else 0
        async with get_session() as session:
            appointment_repo = AppointmentRepository(session)
            appointment = await appointment_repo.get_appointment_by_id(cita_id, doctor_id)
            if not appointment:
                await query.edit_message_text(
                    "❌ Cita no encontrada.",
                    parse_mode="HTML"
                )
                return True

            dt = datetime.fromtimestamp(appointment["start_ts"])
            text = (
                f"📋 <b>Detalle de la cita #{appointment['id']}</b>\n\n"
                f"👤 <b>Paciente:</b> {escape_html(appointment['patient_name'] or str(appointment['patient_telegram_id']))}\n"
                f"🗓️ <b>Fecha:</b> {dt.strftime('%d/%m/%Y')}\n"
                f"⏰ <b>Hora:</b> {dt.strftime('%H:%M')}\n"
                f"📍 <b>Ubicación:</b> {escape_html(appointment['location'] or 'Pendiente')}\n"
                f"🎯 <b>Motivo:</b> {escape_html(appointment['reason'] or 'No especificado')}\n"
                f"ℹ️ <b>Estado:</b> {appointment['status'].capitalize()}\n"
            )

            reply_markup = keyboards.get_cita_detail_keyboard(cita_id, filter_type, page_index)
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
            return True
        return True
async def confirm_appointment_and_notify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    if not query:
        return True
    await query.answer()

    parts = query.data.split('_')
    cita_id = int(parts[3])
    filter_type = parts[4]
    page_index = int(parts[5])

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text(
            "⚠️ Solo los médicos activos pueden gestionar citas.",
            parse_mode="HTML"
        )
        return True

    async with get_session() as session:
        appointment_repo = AppointmentRepository(session)
        appointment = await appointment_repo.get_appointment_by_id(cita_id, doctor_id)
        if not appointment:
            await query.edit_message_text("❌ Cita no encontrada.", parse_mode="HTML")
            return True

        if not await appointment_repo.update_appointment_status(cita_id, doctor_id, "confirmed"):
            await query.answer("⚠️ No se pudo actualizar la cita.", show_alert=True)
            return True

        # Si la actualización fue exitosa, enviar notificación al paciente
        patient_id = appointment["patient_telegram_id"]
        dt = datetime.fromtimestamp(appointment["start_ts"])
        confirmation_text = (
            f"✅ <b>¡Tu cita ha sido confirmada!</b>\n\n"
            f"🗓️ <b>Fecha:</b> {dt.strftime('%d/%m/%Y')}\n"
            f"⏰ <b>Hora:</b> {dt.strftime('%H:%M')}\n"
            f"📍 <b>Ubicación:</b> {escape_html(appointment['location'] or 'Pendiente')}\n"
            f"🎯 <b>Motivo:</b> {escape_html(appointment['reason'] or 'No especificado')}\n\n"
            f"Para agilizar el proceso, y hacerlo más fluido, por favor <b>DEBES</b> completar tu historia médica de preconsulta.\n"
        )

        # Teclado con botón de preconsulta
        preconsulta_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Llenar Preconsulta", callback_data=f"preconsulta_start_{cita_id}")]
        ])

        try:
            await context.bot.send_message(
                chat_id=patient_id,
                text=confirmation_text,
                parse_mode=ParseMode.HTML,
                reply_markup=preconsulta_keyboard
            )
        except Exception as exc:
            logger.warning(f"No se pudo notificar al paciente {patient_id}: {exc}")

    await query.answer("✅ Cita confirmada.", show_alert=True)
    await _redirect_to_list(query, update, context, filter_type, page_index)
    return True

# --- FUNCIÓN 'action_handler' MODIFICADA ---
async def action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.edit_message_text(
            "⚠️ Solo los médicos activos pueden gestionar citas.",
            parse_mode="HTML"
        )
        return

    parts = query.data.split('_')
    action = parts[2]
    cita_id = int(parts[3])
    filter_type = parts[4]
    page_index = int(parts[5])
    logger.info(f"[citas] action={action} cita={cita_id} filtro={filter_type} pag={page_index}")

    async with get_session() as session:
        appointment_repo = AppointmentRepository(session)
        appointment = await appointment_repo.get_appointment_by_id(cita_id, doctor_id)
        if not appointment:
            await query.edit_message_text("❌ Cita no encontrada.", parse_mode="HTML")
            return

        if action == "confirm":
            await confirm_appointment_and_notify(update, context)
            return

        if action == "reschedule":
            context.user_data["reschedule_context"] = {
                "cita_id": cita_id,
                "filter_type": filter_type,
                "page_index": page_index,
                "doctor_id": doctor_id,
            }
            calendar = CustomCalendar().create_reschedule_calendar(cita_id, filter_type, page_index)
            await query.message.edit_text(
                "📅 Selecciona la nueva fecha:",
                reply_markup=calendar
            )
            return

        # Acciones directas sobre el estado
        status_map = {
            "complete": ("completed", "✅ Cita marcada como completada."),
            "cancel": ("cancelled", "❌ Cita cancelada."),
        }

        if action in status_map:
            new_status, toast = status_map[action]
            success = await appointment_repo.update_appointment_status(cita_id, doctor_id, new_status)
            if success and action == "cancel":
                try:
                    await context.bot.send_message(
                        chat_id=appointment["patient_telegram_id"],
                        text="⚠️ Tu cita ha sido cancelada. Por favor, contacta a tu doctora para reprogramar.",
                    )
                except Exception as exc:
                    logger.warning(f"No se pudo notificar cancelación al paciente {appointment['patient_telegram_id']}: {exc}")
            await query.answer(toast if success else "⚠️ No se pudo actualizar la cita.", show_alert=not success)
            await _redirect_to_list(query, update, context, filter_type, page_index)
            return

        if action == "delete":
            success = await appointment_repo.delete_appointment(cita_id, doctor_id)
        await query.answer("🗑️ Cita eliminada." if success else "⚠️ No se pudo eliminar la cita.", show_alert=not success)
        await _redirect_to_list(query, update, context, filter_type, page_index)
        return

    await query.answer("⚠️ Acción no soportada.", show_alert=True)


async def calendar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    if not query:
        logger.warning("[citas] calendar_handler: No hay query")
        return True
    await query.answer()
    data = query.data
    logger.info(f"[citas] calendario -> {data}")

    reschedule_context = context.user_data.get("reschedule_context")
    if not reschedule_context:
        await query.edit_message_text("⚠️ Sesión expirada.")
        return True

    doctor_id = reschedule_context["doctor_id"]
    cita_id = reschedule_context["cita_id"]
    filter_type = reschedule_context["filter_type"]
    page_index = reschedule_context["page_index"]

    if data.startswith("resched_cal_nav_"):
        year, month = map(int, data.split('_')[-1].split('-'))
        calendar = CustomCalendar().create_reschedule_calendar(cita_id, filter_type, page_index, year=year, month=month)
        await query.message.edit_reply_markup(reply_markup=calendar)
        return True

    if data.startswith("resched_cal_day_"):
        selected_date = CustomCalendar().process_selection(data)
        if not selected_date:
            return True
        context.user_data["reschedule_date"] = selected_date.isoformat()
        times_keyboard = await keyboards.get_reschedule_time_slots_keyboard(
            doctor_id,
            selected_date.isoformat(),
            cita_id,
            filter_type,
            page_index,
            "doctor",
        )
        await query.message.edit_text(
            f"📅 Fecha seleccionada: <b>{selected_date.strftime('%d/%m/%Y')}</b>\n\n⏰ Selecciona una nueva hora:",
            reply_markup=times_keyboard,
            parse_mode=ParseMode.HTML,
        )
        return True

    if data == "resched_cal_keep_date":
        context.user_data.pop("reschedule_context", None)
        context.user_data.pop("reschedule_date", None)
        await _redirect_to_list(query, update, context, filter_type, page_index)
        return True

    if data == "resched_cal_cancel":
        context.user_data.pop("reschedule_context", None)
        context.user_data.pop("reschedule_date", None)
        await _redirect_to_list(query, update, context, filter_type, page_index)
        return True

    return True


async def reschedule_time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    query = update.callback_query
    if not query:
        return True
    await query.answer()
    reschedule_context = context.user_data.get("reschedule_context")
    selected_date = context.user_data.get("reschedule_date")
    if not reschedule_context or not selected_date:
        await query.edit_message_text("⚠️ Sesión expirada.")
        return True
    logger.info(f"[citas] seleccionar hora -> {query.data} ({reschedule_context})")

    data = query.data
    if data.startswith("reschedule_back_to_calendar"):
        calendar = CustomCalendar().create_reschedule_calendar(
            reschedule_context["cita_id"],
            reschedule_context["filter_type"],
            reschedule_context["page_index"],
        )
        await query.message.edit_text("📅 Selecciona la nueva fecha:", reply_markup=calendar)
        return True

    if not data.startswith("reschedule_time_"):
        await query.answer("⚠️ Selección inválida.", show_alert=True)
        return True

    parts = data.split('_')
    selected_time = parts[2]
    cita_id = int(parts[3])
    filter_type = parts[4]
    page_index = int(parts[5])
    doctor_id = reschedule_context["doctor_id"]

    try:
        dt = datetime.strptime(f"{selected_date} {selected_time}", "%Y-%m-%d %H:%M")
        new_ts = int(dt.timestamp())
    except ValueError:
        await query.answer("⚠️ Hora inválida.", show_alert=True)
        return True

    async with get_session() as session:
        appointment_repo = AppointmentRepository(session)
        success = await appointment_repo.update_appointment_time(cita_id, doctor_id, new_ts)
    if not success:
        await query.answer("⚠️ No se pudo reagendar la cita.", show_alert=True)
        return True

    context.user_data.pop("reschedule_context", None)
    context.user_data.pop("reschedule_date", None)

    await query.answer("✅ Cita reagendada.", show_alert=True)
    await _redirect_to_list(query, update, context, filter_type, page_index)
    return True
async def send_admin_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Función que ejecuta el job para reenviar la notificación al admin."""
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    notification_text = job_data["notification_text"]
    appointment_id = job_data["appointment_id"]

    # Reconstruimos el teclado original de la notificación
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏰ Recuérdame más tarde", callback_data=f"appt_remind_later_{appointment_id}"),
            InlineKeyboardButton("🗑️ Descartar", callback_data=f"appt_dismiss_{appointment_id}")
        ]
    ])

    await context.bot.send_message(
        chat_id=chat_id,
        text=notification_text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

async def handle_remind_me_later(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Programa un recordatorio para más tarde (30 minutos)."""
    query = update.callback_query
    await query.answer("⏰ Te recordaré en 30 minutos.", show_alert=False)
    
    try:
        # Extraer appointment_id del callback_data
        appointment_id = int(query.data.split('_')[-1])
        
        # Obtener doctor_id del usuario actual
        user_id = update.effective_user.id
        doctor_id = await _get_doctor_id(update)
        
        if not doctor_id:
            await query.message.edit_text("❌ Error: No se pudo identificar tu perfil.")
            return
        
        # Obtener datos de la cita para reconstruir la notificación
        async with get_session() as session:
            appointment_repo = AppointmentRepository(session)
            appointment = await appointment_repo.get_appointment_by_id(appointment_id, doctor_id)
            if not appointment:
                await query.message.edit_text("❌ Error: No se encontró la cita.")
                return
            
            # Convertir Row a dict si es necesario
            if hasattr(appointment, 'keys'):
                appt_dict = dict(appointment)
            else:
                appt_dict = appointment
            
            # Reconstruir el texto de la notificación
            from datetime import datetime
            dt = datetime.fromtimestamp(appt_dict.get('start_ts', 0))
            notification_text = (
                f"🗓️ <b>¡Nueva Cita Agendada!</b>\n\n"
                + f"👤 <b>Paciente:</b> {escape_html(appt_dict.get('patient_name', 'N/A'))}\n\n"
                + f"<b>Detalles de la Cita:</b>\n"
                + f"<blockquote>"
                + f"🎯 <b>Tipo:</b> {escape_html(appt_dict.get('consultation_type', 'N/A'))}\n"
                + f"🗓️ <b>Fecha:</b> {dt.strftime('%Y-%m-%d')}\n"
                + f"⏰ <b>Hora:</b> {dt.strftime('%H:%M')}\n"
                + f"📍 <b>Ubicación:</b> {escape_html(appt_dict.get('location', 'N/A'))}"
                + f"</blockquote>"
            )
            
            # Programar recordatorio para 30 minutos después
            from datetime import timedelta
            when = datetime.now() + timedelta(minutes=30)
            
            context.job_queue.run_once(
                send_admin_reminder,
                when=when,
                data={
                    "chat_id": query.message.chat_id,
                "notification_text": notification_text,
                "appointment_id": appointment_id
            }
        )
        
        # Borrar el mensaje actual
        try:
            await query.message.delete()
        except:
            pass
            
    except (ValueError, IndexError) as e:
        logger.error(f"Error al procesar recordatorio: {e}")
        await query.answer("❌ Error al programar el recordatorio.", show_alert=True)

async def handle_dismiss_notification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Descarta la notificación borrando el mensaje."""
    query = update.callback_query
    await query.answer("🗑️ Notificación descartada.", show_alert=False)
    try:
        await query.message.delete()
    except Exception as e:
        logger.warning(f"No se pudo borrar el mensaje: {e}")

def register(app: Application):
    """Registra todos los handlers de gestión de citas en la aplicación del bot."""
    # Handlers básicos registrados - las funciones son stubs temporales
    app.add_handler(CallbackQueryHandler(list_and_detail_handler, pattern='^citas_(view|detail)_'))
    app.add_handler(CallbackQueryHandler(action_handler, pattern='^citas_(action|confirm)_'))
    app.add_handler(CallbackQueryHandler(calendar_handler, pattern='^resched_cal_'))
    app.add_handler(CallbackQueryHandler(reschedule_time_handler, pattern='^reschedule_'))
    app.add_handler(CallbackQueryHandler(handle_remind_me_later, pattern='^appt_remind_later_'))
    app.add_handler(CallbackQueryHandler(handle_dismiss_notification, pattern='^appt_dismiss_'))