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

def escape_html(text: str) -> str:
    return html.escape(str(text))

async def _get_doctor_id(update: Update) -> int:
    user_id = update.effective_user.id
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    return doctor[0] if doctor else None

# --- NUEVA FUNCIÓN DE RENDERIZADO CENTRALIZADA (Inspirada en el bot viejo) ---

async def render_citas_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, view: str, **kwargs):
    query = update.callback_query
    # await query.answer() # --- ESTA LÍNEA SE HA ELIMINADO ---

    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        if query:
            await query.answer() # Respondemos al query antes de editar
        await query.edit_message_text("⚠️ Solo los médicos activos pueden gestionar citas.")
        return

    text, reply_markup = "", None

    if view == 'list':
        filter_type = kwargs.get('filter_type', 'all-pending')
        page_index = kwargs.get('page_index', 0)

        async with get_session() as session:
            repo = AppointmentRepository(session)
            statuses = {"pending": ["pending"], "confirmed": ["confirmed"], "completed": ["completed"]}.get(filter_type)
            all_citas = await repo.get_appointments_for_doctor(doctor_id, statuses)

        citas_formatted = []
        for apt in all_citas:
            dt = datetime.fromtimestamp(apt["start_ts"])
            descripcion = f"{dt.strftime('%d/%m/%Y %H:%M')} - {escape_html(apt['patient_name'] or 'N/A')}"
            if apt.get("reason"):
                descripcion += f" ({escape_html(apt['reason'])})"
            citas_formatted.append({"id": apt["id"], "descripcion": descripcion})

        total_citas = len(citas_formatted)
        start_index = page_index * CITAS_PER_PAGE
        citas_paginadas = citas_formatted[start_index : start_index + CITAS_PER_PAGE]

        if not all_citas:
            filter_translations = {
                'all-pending': "pendientes",
                'pending': "pendientes",
                'confirmed': "confirmadas",
                'completed': "completadas"
            }
            friendly_filter_name = filter_translations.get(filter_type, filter_type)
            text = f"👍 No hay citas {friendly_filter_name} por el momento."
        else:
            total_paginas = max(1, (total_citas + CITAS_PER_PAGE - 1) // CITAS_PER_PAGE)
            text = f"<b>📅 Citas Encontradas</b> (Página {page_index + 1}/{total_paginas})"

        reply_markup = keyboards.get_citas_list_keyboard(citas_paginadas, page_index, total_citas, filter_type)

    elif view == 'detail':
        cita_id = kwargs.get('cita_id')
        async with get_session() as session:
            repo = AppointmentRepository(session)
            appointment = await repo.get_appointment_by_id(cita_id, doctor_id)

        if appointment:
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
            reply_markup = keyboards.get_cita_detail_keyboard(cita_id, kwargs.get('filter_type'), kwargs.get('page_index'))
        else:
            text = "❌ Cita no encontrada o ya no está disponible."
            # Mostramos la alerta aquí porque es un feedback de una acción implícita
            await query.answer(text, show_alert=True)
            # Y llamamos a la función de nuevo para volver a la lista
            # Pasamos el query original en un nuevo objeto update para que la recursión funcione
            proxy_update = type('obj', (object,), {'callback_query': query, 'effective_user': update.effective_user, 'effective_chat': update.effective_chat})()
            return await render_citas_panel(proxy_update, context, 'list', **kwargs)

    elif view == 'confirm_action':
        action = kwargs.get('action')
        text = f"⚠️ <b>¿Seguro que quieres {action.upper()} esta cita?</b>"
        reply_markup = keyboards.get_cita_confirm_action_keyboard(
            action=action, cita_id=kwargs.get('cita_id'),
            filter_type=kwargs.get('filter_type'), page_index=kwargs.get('page_index')
        )

    try:
        # Solo editamos si hay un query y un mensaje asociado
        if query and query.message:
            await query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode="HTML")
    except BadRequest as e:
        if "message is not modified" not in str(e).lower():
            logger.warning(f"Error en render_citas_panel: {e}")
async def _confirm_and_notify(context: ContextTypes.DEFAULT_TYPE, cita_id: int, doctor_id: int) -> bool:
    """
    Actualiza el estado de la cita a 'confirmada', notifica al paciente,
    y devuelve True si la actualización en la BD fue exitosa.
    """
    async with get_session() as session:
        repo = AppointmentRepository(session)

        # 1. Actualizamos el estado de la cita en la base de datos
        if not await repo.update_appointment_status(cita_id, doctor_id, "confirmed"):
            logger.error(f"Fallo al actualizar el estado de la cita {cita_id} a 'confirmed'.")
            return False

        # 2. Obtenemos los detalles de la cita para la notificación
        appointment = await repo.get_appointment_by_id(cita_id, doctor_id)
        if not appointment:
            # Esto es improbable si el paso anterior funcionó, pero es una buena práctica de seguridad
            logger.warning(f"Cita {cita_id} confirmada en BD, pero no se encontraron detalles para notificar.")
            return True # La acción principal (confirmar) fue exitosa

        # 3. Intentamos enviar la notificación al paciente
        try:
            patient_id = appointment["patient_telegram_id"]
            dt = datetime.fromtimestamp(appointment["start_ts"])
            confirmation_text = (
                f"✅ <b>¡Tu cita ha sido confirmada!</b>\n\n"
                f"🗓️ <b>Fecha:</b> {dt.strftime('%d/%m/%Y')}\n"
                f"⏰ <b>Hora:</b> {dt.strftime('%H:%M')}\n"
                f"📍 <b>Ubicación:</b> {escape_html(appointment['location'] or 'Pendiente')}\n\n"
                f"Para agilizar el proceso, por favor completa tu historia médica de preconsulta."
            )
            preconsulta_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Llenar Preconsulta", callback_data=f"preconsulta_start_{cita_id}")]
            ])
            await context.bot.send_message(
                chat_id=patient_id, text=confirmation_text,
                parse_mode=ParseMode.HTML, reply_markup=preconsulta_keyboard
            )
            logger.info(f"Notificación de confirmación enviada al paciente {patient_id} para la cita {cita_id}.")
        except Exception as exc:
            # La cita se confirmó, pero la notificación falló. Logueamos el error pero no consideramos la operación un fracaso total.
            logger.error(f"Se confirmó la cita {cita_id} pero no se pudo notificar al paciente {patient_id}: {exc}")

    return True # Devuelve True porque la cita fue confirmada en la base de datos


'''
async def _confirm_and_notify(context: ContextTypes.DEFAULT_TYPE, cita_id: int, doctor_id: int) -> bool:
    """Actualiza el estado de la cita a 'confirmada' y notifica al paciente."""
    async with get_session() as session:
        repo = AppointmentRepository(session)
        appointment = await repo.get_appointment_by_id(cita_id, doctor_id)
        if not appointment:
            logger.warning(f"Intento de confirmar una cita ({cita_id}) no encontrada para el doctor {doctor_id}.")
            return False

        if not await repo.update_appointment_status(cita_id, doctor_id, "confirmed"):
            logger.error(f"Fallo al actualizar el estado de la cita {cita_id} a 'confirmed'.")
            return False

        # Si la actualización fue exitosa, enviar notificación al paciente
        try:
            patient_id = appointment["patient_telegram_id"]
            dt = datetime.fromtimestamp(appointment["start_ts"])
            confirmation_text = (
                f"✅ <b>¡Tu cita ha sido confirmada!</b>\n\n"
                f"🗓️ <b>Fecha:</b> {dt.strftime('%d/%m/%Y')}\n"
                f"⏰ <b>Hora:</b> {dt.strftime('%H:%M')}\n"
                f"📍 <b>Ubicación:</b> {escape_html(appointment['location'] or 'Pendiente')}\n\n"
                f"Para agilizar el proceso, por favor completa tu historia médica de preconsulta."
            )
            preconsulta_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Llenar Preconsulta", callback_data=f"preconsulta_start_{cita_id}")]
            ])
            await context.bot.send_message(
                chat_id=patient_id, text=confirmation_text,
                parse_mode=ParseMode.HTML, reply_markup=preconsulta_keyboard
            )
            return True
        except Exception as exc:
            logger.error(f"No se pudo notificar al paciente {patient_id}: {exc}")
            # La cita se confirmó pero la notificación falló. Devolvemos True pero con un error logueado.
            return True'''
async def _confirm_and_notify(context: ContextTypes.DEFAULT_TYPE, cita_id: int, doctor_id: int) -> bool:
    """
    Actualiza el estado de la cita a 'confirmada' y notifica al paciente.
    Devuelve True si todo fue exitoso, False en caso contrario.
    """
    async with get_session() as session:
        repo = AppointmentRepository(session)
        # 1. Actualizamos el estado primero
        if not await repo.update_appointment_status(cita_id, doctor_id, "confirmed"):
            logger.error(f"Fallo al actualizar el estado de la cita {cita_id} a 'confirmed'.")
            return False

        # 2. Obtenemos los detalles para la notificación
        appointment = await repo.get_appointment_by_id(cita_id, doctor_id)
        if not appointment:
            logger.warning(f"Cita {cita_id} confirmada pero no se encontraron detalles para notificar.")
            return True # La acción principal fue exitosa

        # 3. Intentamos notificar al paciente
        try:
            patient_id = appointment["patient_telegram_id"]
            dt = datetime.fromtimestamp(appointment["start_ts"])
            confirmation_text = (
                f"✅ <b>¡Tu cita ha sido confirmada!</b>\n\n"
                f"🗓️ <b>Fecha:</b> {dt.strftime('%d/%m/%Y')}\n"
                f"⏰ <b>Hora:</b> {dt.strftime('%H:%M')}\n"
                f"📍 <b>Ubicación:</b> {escape_html(appointment['location'] or 'Pendiente')}\n\n"
                f"Para agilizar el proceso, por favor completa tu historia médica de preconsulta."
            )
            preconsulta_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Llenar Preconsulta", callback_data=f"preconsulta_start_{cita_id}")]
            ])
            await context.bot.send_message(
                chat_id=patient_id, text=confirmation_text,
                parse_mode=ParseMode.HTML, reply_markup=preconsulta_keyboard
            )
        except Exception as exc:
            logger.error(f"Se confirmó la cita {cita_id} pero no se pudo notificar al paciente {patient_id}: {exc}")

    return True
# --- HANDLERS PRINCIPALES (Ahora llaman a render_citas_panel) ---

async def doctor_citas_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Punto de entrada al menú de citas del doctor."""
    await render_citas_panel(update, context, 'list', filter_type='all-pending', page_index=0)

async def list_and_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejador para navegar entre la lista y el detalle."""
    query = update.callback_query
    parts = query.data.split('_')
    view_type, args = parts[1], parts[2:]

    kwargs = {}
    if view_type == 'view':
        kwargs['filter_type'] = args[0]
        kwargs['page_index'] = int(args[1])
        await render_citas_panel(update, context, 'list', **kwargs)
    elif view_type == 'detail':
        kwargs['cita_id'] = int(args[0])
        kwargs['filter_type'] = args[1]
        kwargs['page_index'] = int(args[2])
        await render_citas_panel(update, context, 'detail', **kwargs)
'''
async def action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador para todas las acciones sobre una cita (confirmar, completar, cancelar, reagendar, eliminar)."""
    query = update.callback_query

    parts = query.data.split('_')
    action_type = parts[1]  # 'action' o 'confirm'
    action = parts[2]
    cita_id = int(parts[3])
    filter_type = parts[4]
    page_index = int(parts[5])

    ctx = {'cita_id': cita_id, 'filter_type': filter_type, 'page_index': page_index, 'action': action}
    doctor_id = await _get_doctor_id(update)
    feedback_text = None

    if action_type == 'action':
        # Este bloque maneja el PRIMER clic en un botón de acción
        await query.answer()

        if action == 'reschedule':
            context.user_data["reschedule_context"] = {
                "cita_id": cita_id, "filter_type": filter_type, "page_index": page_index,
                "doctor_id": doctor_id,
            }
            async with get_session() as session:
                repo = AppointmentRepository(session)
                appointment = await repo.get_appointment_by_id(cita_id, doctor_id)

            highlight_date = datetime.fromtimestamp(appointment["start_ts"]).date() if appointment else None

            calendar = CustomCalendar().create_reschedule_calendar(
                cita_id, filter_type, page_index, highlight_date=highlight_date
            )
            await query.message.edit_text("📅 Selecciona la nueva fecha para reagendar:", reply_markup=calendar)
            return

        elif action == 'confirm':
            success = await _confirm_and_notify(context, cita_id, doctor_id)
            feedback_text = "✅ Cita confirmada y paciente notificado." if success else "❌ Error al confirmar la cita."
            await query.answer(feedback_text, show_alert=True)
            # Después de confirmar, redibujamos la lista para que la cita desaparezca del filtro 'pending'
            return await render_citas_panel(update, context, 'list', filter_type=filter_type, page_index=page_index)

        elif action == 'complete':
            async with get_session() as session:
                repo = AppointmentRepository(session)
                success = await repo.update_appointment_status(cita_id, doctor_id, 'completed')
            feedback_text = "✅ Cita marcada como completada." if success else "❌ Error al actualizar."
            await query.answer(feedback_text, show_alert=True)
            # Redibujamos la lista para que desaparezca de filtros activos
            return await render_citas_panel(update, context, 'list', filter_type=filter_type, page_index=page_index)

        elif action in ['delete', 'cancel']:
            # Para acciones peligrosas, mostramos la pantalla de confirmación
            return await render_citas_panel(update, context, 'confirm_action', **ctx)

    elif action_type == 'confirm':
        # Este bloque maneja el SEGUNDO clic (el botón "Sí, CONFIRMAR")
        async with get_session() as session:
            repo = AppointmentRepository(session)
            if action == 'delete':
                success = await repo.delete_appointment(cita_id, doctor_id)
                feedback_text = "🗑️ Cita eliminada." if success else "❌ Error al eliminar."
            elif action == 'cancel':
                success = await repo.update_appointment_status(cita_id, doctor_id, 'cancelled')
                feedback_text = "❌ Cita cancelada." if success else "❌ Error al cancelar."
                # (Aquí iría la notificación al paciente sobre la cancelación)

        if feedback_text:
            await query.answer(feedback_text, show_alert=True)

        # Después de cualquier acción confirmada, SIEMPRE redibujamos la lista
        await render_citas_panel(update, context, 'list', filter_type=filter_type, page_index=page_index)'''
'''
# Helper para obtener doctor_id
async def _get_doctor_id(update: Update) -> int:
    """Obtiene el doctor_id del usuario actual."""
    user_id = update.effective_user.id
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    return doctor[0] if doctor else None'''

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
'''
async def doctor_citas_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Redirige directamente a la lista de citas usando un callback proxy."""
    original_query = update.callback_query
    if not original_query:
        return

    await original_query.answer()

    proxy_update = _build_proxy_update(original_query, "citas_view_all-pending_0", update)
    await list_and_detail_handler(proxy_update, context)


# TODO: Adaptar funciones restantes para multi-tenant
# Las siguientes funciones están comentadas temporalmente hasta adaptarlas completamente'''
"""
# @admin_required  # TODO: Adaptar para multi-tenant
async def force_reminders_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Comentado temporalmente - necesita adaptación
    pass
"""



# Funciones adaptadas para multi-tenant
'''
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
        return True'''

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
'''async def action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    await query.answer("⚠️ Acción no soportada.", show_alert=True)'''

async def action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador para todas las acciones sobre una cita (confirmar, completar, cancelar, reagendar, eliminar)."""
    query = update.callback_query

    parts = query.data.split('_')
    action_type = parts[1]  # 'action' o 'confirm'
    action = parts[2]
    cita_id = int(parts[3])
    filter_type = parts[4]
    page_index = int(parts[5])

    ctx = {'cita_id': cita_id, 'filter_type': filter_type, 'page_index': page_index, 'action': action}
    doctor_id = await _get_doctor_id(update)
    feedback_text = None

    if action_type == 'action':
        # Este bloque maneja el PRIMER clic en un botón de acción desde la vista de detalle.

        if action == 'reschedule':
            await query.answer() # Respuesta silenciosa para que el reloj de espera desaparezca
            context.user_data["reschedule_context"] = {
                "cita_id": cita_id, "filter_type": filter_type, "page_index": page_index,
                "doctor_id": doctor_id,
            }
            async with get_session() as session:
                repo = AppointmentRepository(session)
                appointment = await repo.get_appointment_by_id(cita_id, doctor_id)

            highlight_date = datetime.fromtimestamp(appointment["start_ts"]).date() if appointment else None

            calendar = CustomCalendar().create_reschedule_calendar(
                cita_id, filter_type, page_index, highlight_date=highlight_date
            )
            await query.message.edit_text("📅 Selecciona la nueva fecha para reagendar:", reply_markup=calendar)
            return

        elif action == 'confirm':
            success = await _confirm_and_notify(context, cita_id, doctor_id)
            feedback_text = "✅ Cita confirmada y paciente notificado." if success else "❌ Error al confirmar la cita."
            await query.answer(feedback_text, show_alert=True)
            # Después de confirmar, redibujamos la lista para que la cita desaparezca del filtro 'pending'
            return await render_citas_panel(update, context, 'list', filter_type=filter_type, page_index=page_index)

        elif action == 'complete':
            async with get_session() as session:
                repo = AppointmentRepository(session)
                success = await repo.update_appointment_status(cita_id, doctor_id, 'completed')
            feedback_text = "✅ Cita marcada como completada." if success else "❌ Error al actualizar."
            await query.answer(feedback_text, show_alert=True)
            # Redibujamos la lista para que desaparezca de filtros activos
            return await render_citas_panel(update, context, 'list', filter_type=filter_type, page_index=page_index)

        elif action in ['delete', 'cancel']:
            await query.answer() # Respuesta silenciosa para cambiar de vista
            # Para acciones peligrosas, mostramos la pantalla de confirmación
            return await render_citas_panel(update, context, 'confirm_action', **ctx)

    elif action_type == 'confirm':
        # Este bloque maneja el SEGUNDO clic (el botón "Sí, CONFIRMAR" de la pantalla de confirmación).
        async with get_session() as session:
            repo = AppointmentRepository(session)
            if action == 'delete':
                success = await repo.delete_appointment(cita_id, doctor_id)
                feedback_text = "🗑️ Cita eliminada." if success else "❌ Error al eliminar."
            elif action == 'cancel':
                success = await repo.update_appointment_status(cita_id, doctor_id, 'cancelled')
                feedback_text = "❌ Cita cancelada." if success else "❌ Error al cancelar."
                # (Aquí podrías añadir la notificación al paciente sobre la cancelación si lo deseas)

        if feedback_text:
            await query.answer(feedback_text, show_alert=True)

        # Después de cualquier acción confirmada, SIEMPRE redibujamos la lista
        await render_citas_panel(update, context, 'list', filter_type=filter_type, page_index=page_index)


async def calendar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    data = query.data
    logger.info(f"[citas] calendario -> {data}")

    reschedule_context = context.user_data.get("reschedule_context")
    if not reschedule_context:
        await query.edit_message_text("⚠️ Sesión expirada. Por favor, vuelve a empezar.")
        return

    # Extraemos el contexto para usarlo
    cita_id = reschedule_context["cita_id"]
    filter_type = reschedule_context["filter_type"]
    page_index = reschedule_context["page_index"]

    if data.startswith("resched_cal_nav_"):
        year, month = map(int, data.split('_')[-1].split('-'))
        calendar = CustomCalendar().create_reschedule_calendar(cita_id, filter_type, page_index, year=year, month=month)
        await query.message.edit_reply_markup(reply_markup=calendar)
        return

    if data.startswith("resched_cal_day_"):
        selected_date = CustomCalendar().process_selection(data)
        if not selected_date:
            return
        context.user_data["reschedule_date"] = selected_date.isoformat()
        times_keyboard = await keyboards.get_reschedule_time_slots_keyboard(
            reschedule_context["doctor_id"], selected_date.isoformat(),
            cita_id, filter_type, page_index, "doctor"
        )
        await query.message.edit_text(
            f"📅 Fecha seleccionada: <b>{selected_date.strftime('%d/%m/%Y')}</b>\n\n⏰ Selecciona una nueva hora:",
            reply_markup=times_keyboard,
            parse_mode=ParseMode.HTML,
        )
        return

    # --- CORRECCIÓN EN CANCELACIÓN Y MANTENER FECHA ---
    # Si se cancela o se mantiene, limpiamos user_data y volvemos a la lista usando render_citas_panel
    if data == "resched_cal_keep_date" or data == "resched_cal_cancel":
        context.user_data.pop("reschedule_context", None)
        context.user_data.pop("reschedule_date", None)
        # Volvemos a la vista de detalle de la cita original
        await render_citas_panel(update, context, 'detail', cita_id=cita_id, filter_type=filter_type, page_index=page_index)
        return

async def reschedule_time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    reschedule_context = context.user_data.get("reschedule_context")
    selected_date = context.user_data.get("reschedule_date")

    if not reschedule_context or not selected_date:
        await query.answer()
        await query.edit_message_text("⚠️ Sesión expirada. Por favor, vuelve a empezar.")
        return

    data = query.data

    # Manejar el botón "Elegir otra fecha"
    if data.startswith("reschedule_back_to_calendar"):
        await query.answer()
        calendar = CustomCalendar().create_reschedule_calendar(
            reschedule_context["cita_id"], reschedule_context["filter_type"], reschedule_context["page_index"]
        )
        await query.message.edit_text("📅 Selecciona la nueva fecha:", reply_markup=calendar)
        return

    if not data.startswith("reschedule_time_"):
        await query.answer("⚠️ Selección inválida.", show_alert=True)
        return

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
        await query.answer("⚠️ Formato de hora inválido.", show_alert=True)
        return

    # Actualizamos la cita en la base de datos
    async with get_session() as session:
        appointment_repo = AppointmentRepository(session)
        success = await appointment_repo.update_appointment_time(cita_id, doctor_id, new_ts)

    if not success:
        await query.answer("⚠️ No se pudo reagendar la cita en la base de datos.", show_alert=True)
        return

    # Limpiamos los datos de la conversación de reagendamiento
    context.user_data.pop("reschedule_context", None)
    context.user_data.pop("reschedule_date", None)

    # Mostramos la alerta de éxito
    await query.answer("✅ ¡Cita reagendada con éxito!", show_alert=True)

    # Finalmente, refrescamos la vista de la lista de citas
    await render_citas_panel(update, context, 'list', filter_type=filter_type, page_index=page_index)
'''
async def reschedule_time_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()

    reschedule_context = context.user_data.get("reschedule_context")
    selected_date = context.user_data.get("reschedule_date")
    if not reschedule_context or not selected_date:
        await query.edit_message_text("⚠️ Sesión expirada. Por favor, vuelve a empezar.")
        return

    data = query.data

    # Manejar el botón "Elegir otra fecha"
    if data.startswith("reschedule_back_to_calendar"):
        calendar = CustomCalendar().create_reschedule_calendar(
            reschedule_context["cita_id"], reschedule_context["filter_type"], reschedule_context["page_index"]
        )
        await query.message.edit_text("📅 Selecciona la nueva fecha:", reply_markup=calendar)
        return

    if not data.startswith("reschedule_time_"):
        await query.answer("⚠️ Selección inválida.", show_alert=True)
        return

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
        return

    # Actualizamos la base de datos
    async with get_session() as session:
        appointment_repo = AppointmentRepository(session)
        success = await appointment_repo.update_appointment_time(cita_id, doctor_id, new_ts)

    if not success:
        await query.answer("⚠️ No se pudo reagendar la cita.", show_alert=True)
        return

    # Limpiamos los datos de la conversación de reagendamiento
    context.user_data.pop("reschedule_context", None)
    context.user_data.pop("reschedule_date", None)

    await query.answer("✅ Cita reagendada con éxito.", show_alert=True)

    # --- CORRECCIÓN FINAL: Usamos render_citas_panel para volver a la lista ---
    await render_citas_panel(update, context, 'list', filter_type=filter_type, page_index=page_index)'''

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
    await query.answer("⏰ Te recordaré en 30 minutos.", show_alert=True)

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
    '''app.add_handler(CallbackQueryHandler(list_and_detail_handler, pattern='^citas_(view|detail)_'))
    app.add_handler(CallbackQueryHandler(action_handler, pattern='^citas_(action|confirm)_'))'''

    app.add_handler(CallbackQueryHandler(doctor_citas_menu, pattern='^doctor_citas$'))
    app.add_handler(CallbackQueryHandler(list_and_detail_handler, pattern='^citas_view_'))
    app.add_handler(CallbackQueryHandler(list_and_detail_handler, pattern='^citas_detail_'))
    app.add_handler(CallbackQueryHandler(action_handler, pattern='^citas_(action|confirm)_'))
    app.add_handler(CallbackQueryHandler(calendar_handler, pattern='^resched_cal_'))
    app.add_handler(CallbackQueryHandler(reschedule_time_handler, pattern='^reschedule_'))
    app.add_handler(CallbackQueryHandler(handle_remind_me_later, pattern='^appt_remind_later_'))
    app.add_handler(CallbackQueryHandler(handle_dismiss_notification, pattern='^appt_dismiss_'))


