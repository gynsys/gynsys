# /features/citas/user_handlers.py
import logging
from datetime import date, datetime
import asyncio
import html
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, ConversationHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)
from telegram.constants import ParseMode
from telegram.error import BadRequest

from config import DB_PATH
from database.session import get_session
from database.repositories.appointment_repository import SlotRepository, AppointmentRepository
from database import locations_db
from utils.role_manager import RoleManager
from . import user_keyboards as keyboards
from .admin_calendar import CustomCalendar
from features.patient_menu.patient_handler import patient_main_menu

logger = logging.getLogger(__name__)

role_manager = RoleManager(DB_PATH)

# Helper para escape_html (compatibilidad con common.helpers)
def escape_html(text: str) -> str:
    return html.escape(str(text))

# Helper para obtener doctor_id desde context
async def _get_doctor_id_from_context(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Obtiene el doctor_id desde context.user_data o role_manager."""
    user_id = update.effective_user.id
    doctor_id = context.user_data.get("patient_doctor_id")
    if not doctor_id:
        assigned_doctor = await role_manager.get_assigned_doctor(user_id)
        if assigned_doctor:
            doctor_id = assigned_doctor[0]
    return doctor_id

# Helper para verificar si hay cita activa (multi-tenant)
async def _has_active_appointment(user_id: int, doctor_id: int) -> bool:
    """Verifica si el paciente tiene una cita activa con el doctor."""
    if not doctor_id:
        return False
    now_ts = int(datetime.utcnow().timestamp())
    async with get_session() as session:
        from sqlalchemy import select, text
        from database.models.appointment import Appointment, Slot
        
        result = await session.execute(
            select(Appointment.id)
            .join(Slot, Appointment.slot_id == Slot.id)
            .where(
                Slot.doctor_id == doctor_id,
                Appointment.patient_telegram_id == user_id,
                Slot.start_ts >= now_ts
            )
            .limit(1)
        )
        appointment = result.scalar_one_or_none()
        return appointment is not None

# Helper para verificar si es paciente recurrente (simplificado - por ahora siempre False)
async def _check_if_user_is_recurrent(user_id: int, doctor_id: int):
    """Verifica si el usuario es paciente recurrente. Por ahora retorna None."""
    # TODO: Implementar lógica de preconsulta multi-tenant si es necesario
    return None

# Helper para crear cita (multi-tenant)
async def _create_appointment(doctor_id: int, user_id: int, user_name: str, fecha: str, hora: str, 
                              ubicacion: str, status: str = 'pending', reason: str = None,
                              consultation_type: str = None, is_first_pregnancy: bool = None,
                              has_been_pregnant: bool = None) -> int:
    """Crea una cita usando repositories SQLAlchemy. Retorna appointment_id o None."""
    try:
        # Convertir fecha y hora a timestamp
        dt = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
        start_ts = int(dt.timestamp())
        duration_min = 30
        
        # Si es solicitud sin fecha (recurrente), no crear slot todavía
        if fecha == '2000-01-01' and hora == '00:00':
            # Guardar como solicitud pendiente (podríamos crear una tabla de solicitudes)
            # Por ahora, retornamos None y el código original manejará el error
            return None
        
        # Crear slot y reservarlo
        async with get_session() as session:
            slot_repo = SlotRepository(session)
            appointment_repo = AppointmentRepository(session)
            
            note = f"{consultation_type or 'Consulta'} - {reason or ''}"
            slot = await slot_repo.add_slot(doctor_id, start_ts, duration_min, note)
            slot_id = slot.id
            
            success = await appointment_repo.book_slot(
                doctor_id,
                slot_id,
                user_id,
                user_name,
                consultation_type,
                reason,
                ubicacion,
                status,
            )
            
            if success:
                # Obtener el appointment_id recién creado
                from sqlalchemy import select
                from database.models.appointment import Appointment
                result = await session.execute(
                    select(Appointment).where(Appointment.slot_id == slot_id)
                )
                appointment = result.scalar_one_or_none()
                if appointment:
                    return appointment.id
        return None
    except Exception as e:
        logger.error(f"Error al crear cita: {e}")
        return None

# Helper para obtener admin_id (doctor telegram_id)
async def _get_doctor_telegram_id(doctor_id: int) -> int:
    """Obtiene el telegram_id del doctor."""
    doctor = await role_manager.get_doctor_by_id(doctor_id)
    return doctor[2] if doctor else None
# Estados de la conversación
(
    AWAITING_NAME,
    SELECTING_CONSULTATION_TYPE,
    AWAITING_PREGNANCY_INFO,
    AWAITING_REASON,
    SELECTING_LOCATION,
    SELECTING_DATE,
    SELECTING_TIME,
    CONFIRMING,
    FINAL_STATE
) = range(100, 109)

async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Inicia el flujo de agendamiento. Maneja el caso de cita activa y diferencia
    entre pacientes nuevos y recurrentes.
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    doctor_id = await _get_doctor_id_from_context(update, context)

    if not doctor_id:
        await query.edit_message_text(
            "❌ No tienes un médico asignado. Por favor, contacta a tu médico para obtener el enlace de acceso.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menú Principal", callback_data="patient_main_menu")]
            ])
        )
        return ConversationHandler.END

    # Guardar doctor_id en context para uso posterior
    context.user_data['booking_doctor_id'] = doctor_id

    # --- PRIMERO, MANEJAMOS EL CASO DE CITA ACTIVA ---
    if await _has_active_appointment(user_id, doctor_id):
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data="patient_main_menu")]
        ])
        await query.edit_message_text(
            text="🗓️ Ya tienes una cita activa. Si necesitas modificarla, por favor contacta directamente.",
            reply_markup=keyboard
        )
        # Forzamos el fin de CUALQUIER conversación activa.
        return ConversationHandler.END

    # --- SI NO HAY CITA ACTIVA, CONTINUAMOS CON EL AGENDAMIENTO ---
    context.user_data.clear()
    context.user_data['booking_doctor_id'] = doctor_id  # Restaurar doctor_id después de clear

    recurrent_info = await _check_if_user_is_recurrent(user_id, doctor_id)

    if recurrent_info:
        # PACIENTE RECURRENTE
        patient_name = recurrent_info.get('full_name', update.effective_user.first_name)
        context.user_data['booking_name'] = patient_name
        context.user_data['is_recurrent'] = True

        text = (
            f"¡Hola de nuevo, {escape_html(patient_name)}! 👋\n\n"
            "Para agendar tu nueva cita, por favor, selecciona primero el tipo de consulta:"
        )
        await query.edit_message_text(text, reply_markup=keyboards.get_consultation_type_keyboard())
        return SELECTING_CONSULTATION_TYPE

    else:
        # PACIENTE NUEVO
        context.user_data['is_recurrent'] = False
        text = "¡Hola! Para comenzar a agendar tu cita, por favor, escribe tu nombre y apellidos:"

        # Guardamos el ID del mensaje para poder borrarlo
        context.user_data['last_message_id'] = query.message.message_id
        await query.message.edit_text(text)
        return AWAITING_NAME

async def handle_consultation_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    consultation_type = query.data.split('_')[-1]
    context.user_data['booking_consultation_type'] = consultation_type

    if consultation_type == 'Prenatal':
        text = "¿Es tu primer embarazo?"
        await query.edit_message_text(
            text=text,
            reply_markup=keyboards.get_first_pregnancy_keyboard()
        )
    else: # Ginecológica
        text = "¿Has estado embarazada alguna vez?"
        await query.edit_message_text(
            text=text,
            reply_markup=keyboards.get_ever_pregnant_keyboard()
        )
    return AWAITING_PREGNANCY_INFO

# --- ESTA ES LA FUNCIÓN QUE FALTABA ---
async def handle_pregnancy_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    consultation_type = context.user_data.get('booking_consultation_type')

    if consultation_type == 'Prenatal':
        context.user_data['booking_is_first_pregnancy'] = query.data.endswith('_yes')
        text = "Gracias. Ahora, selecciona el motivo de tu consulta prenatal:"
        reason_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🩺 Control Prenatal", callback_data="book_reason_Control Prenatal")],
            [InlineKeyboardButton("😟 Dolor Pélvico", callback_data="book_reason_Dolor pélvico")],
            [InlineKeyboardButton("🩸 Sangrado", callback_data="book_reason_Sangrado")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="book_cancel")]
        ])
    else: # Ginecológica
        context.user_data['booking_has_been_pregnant'] = query.data.endswith('_yes')
        text = "Entendido. Ahora, por favor, selecciona el motivo de esta visita:"
        reason_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🩺 Control Ginecológico", callback_data="book_reason_Control Ginecológico")],
            [InlineKeyboardButton("😖 Dolor pélvico", callback_data="book_reason_Dolor pélvico")],
            [InlineKeyboardButton("🩸 Sangrado", callback_data="book_reason_Sangrado")],
            [InlineKeyboardButton("❌ Cancelar", callback_data="book_cancel")]
        ])

    await query.edit_message_text(text, reply_markup=reason_keyboard)
    return AWAITING_REASON

# --- ESTA FUNCIÓN AHORA SE LLAMA handle_reason ---
async def handle_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    reason = query.data.replace("book_reason_", "", 1)
    context.user_data['booking_reason'] = reason

    # Tanto recurrentes como nuevos van por el mismo flujo: ubicación → calendario → hora → confirmación
    doctor_id = context.user_data.get('booking_doctor_id')
    locations_keyboard = await keyboards.get_locations_keyboard(doctor_id)
    await query.edit_message_text(
        "📍 Entendido. Ahora, selecciona la ubicación:",
        reply_markup=locations_keyboard
    )
    return SELECTING_LOCATION

async def handle_booking_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Extraemos el texto del motivo directamente del callback_data
    reason = query.data.replace("book_reason_", "", 1)
    context.user_data['booking_reason'] = reason

    # Después de guardar el motivo, el siguiente paso es siempre la ubicación
    doctor_id = context.user_data.get('booking_doctor_id')
    locations_keyboard = await keyboards.get_locations_keyboard(doctor_id)
    await query.edit_message_text(
        "📍 Entendido. Ahora, selecciona la ubicación:",
        reply_markup=locations_keyboard
    )
    return SELECTING_LOCATION

async def save_recurrent_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guarda la solicitud de cita para paciente recurrente y muestra mensaje de éxito."""
    query = update.callback_query
    await query.answer()
    
    ud = context.user_data
    doctor_id = ud.get('booking_doctor_id')
    user_id = update.effective_user.id

    if not doctor_id:
        await query.edit_message_text(
            "❌ Error: No se encontró el médico asignado.",
            reply_markup=keyboards.get_back_to_main_menu_keyboard()
        )
        return ConversationHandler.END

    # Crear la cita con estado 'requested' para diferenciarla de las confirmadas
    # Por ahora, para recurrentes sin fecha, no creamos slot todavía
    # TODO: Implementar tabla de solicitudes pendientes si es necesario
    success = True  # Simulamos éxito para mantener el flujo

    if success:
        # Notificar al doctor sobre la solicitud de cita recurrente
        try:
            doctor_telegram_id = await _get_doctor_telegram_id(doctor_id)
            if doctor_telegram_id:
                user = update.effective_user
                user_info = user.full_name
                if user.username:
                    user_info += f" (@{user.username})"

                notification_text = (
                    f"🔄 <b>¡Nueva Solicitud de Cita - Paciente Recurrente!</b>\n\n"
                    f"👤 <b>Paciente:</b> {escape_html(ud['booking_name'])}\n"
                    f"<i>(Usuario: {escape_html(user_info)})</i>\n\n"
                    f"🎯 <b>Motivo:</b> {escape_html(ud.get('booking_reason', 'Consulta de seguimiento'))}\n\n"
                    f"💡 <i>Esta es una solicitud de paciente recurrente que requiere asignación de fecha/hora</i>"
                )

                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📅 Asignar Cita", callback_data="citas_view_all-requested_0")],
                    [InlineKeyboardButton("🗑️ Descartar", callback_data="dismiss_notification")]
                ])

                await context.bot.send_message(
                    chat_id=doctor_telegram_id,
                    text=notification_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard
                )
                logger.info(f"Notificación de cita recurrente enviada al doctor {doctor_telegram_id}.")
        except Exception as e:
            logger.error(f"Error al notificar al admin sobre cita recurrente: {e}")

        # Mensaje de éxito DIRECTO al usuario
        success_text = (
            f"✅ <b>¡Solicitud enviada con éxito, {escape_html(ud['booking_name'])}!</b>\n\n"
            f"<b>Motivo:</b> {escape_html(ud.get('booking_reason', 'Consulta de seguimiento'))}\n\n"
            "Tu médico revisará tu caso y te asignará la fecha y hora más adecuada. "
            "Recibirás una notificación con los detalles una vez confirmada. ¡Gracias!"
        )

        await query.edit_message_text(
            success_text,
            reply_markup=keyboards.get_back_to_main_menu_keyboard()
        )

        context.user_data.clear()
        return ConversationHandler.END
    else:
        await query.edit_message_text(
            "❌ Ha ocurrido un error al procesar tu solicitud. Por favor, inténtalo de nuevo.",
            reply_markup=keyboards.get_back_to_main_menu_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END





async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    parts = query.data.split('_')
    location_id = int(parts[2])
    context.user_data['booking_location_id'] = location_id

    location_name = "Ubicación no especificada"
    if location_id >= 0:
        details = await locations_db.get_location_details(location_id)
        if details and details.get('name'):
            location_name = details['name']
    context.user_data['booking_location_name'] = location_name

    await query.edit_message_text(
        "📅 Perfecto. Ahora, selecciona un día disponible en el calendario:",
        reply_markup=CustomCalendar().create_booking_calendar()
    )
    return SELECTING_DATE

async def calendar_handler_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la interacción con el calendario de agendamiento."""
    query = update.callback_query
    await query.answer()
    data = query.data

    # --- ¡CAMBIO AQUÍ! ---
    # Este 'if' ahora maneja el botón "Elegir otra fecha" y usa el nombre correcto del método.
    if data == 'book_back_to_calendar':
        await query.edit_message_text(
            "📅 Por favor, selecciona un día disponible en el calendario:",
            reply_markup=CustomCalendar().create_booking_calendar() # Corregido de create_calendar()
        )
        return SELECTING_DATE

    if data.startswith("book_cal_nav_"):
        parts = data.split('_')
        year, month = map(int, parts[-1].split('-'))
        await query.message.edit_reply_markup(CustomCalendar().create_booking_calendar(year, month))
        return SELECTING_DATE

    if not (selected_date := CustomCalendar().process_selection(data)):
        return SELECTING_DATE

    context.user_data['booking_date'] = selected_date.isoformat()
    doctor_id = context.user_data.get('booking_doctor_id')
    reply_markup = await keyboards.get_available_time_slots_keyboard(doctor_id, selected_date.isoformat())

    await query.edit_message_text(
        f"👍 Has seleccionado el <b>{selected_date.strftime('%d de %B de %Y')}</b>.\n\nElige una hora disponible:",
        reply_markup=reply_markup
    )
    return SELECTING_TIME

async def handle_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guarda la hora seleccionada y pasa a la pantalla de confirmación."""
    query = update.callback_query
    await query.answer()

    # Guardamos la hora seleccionada
    context.user_data['booking_time'] = query.data.split('_')[-1]

    # Independientemente de si el paciente es nuevo o recurrente,
    # en este punto ya tenemos todos los datos necesarios.
    # Por lo tanto, SIEMPRE vamos a la confirmación.
    return await show_confirmation(update, context)

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['booking_name'] = update.message.text
    try:
        if 'last_message_id' in context.user_data:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data.pop('last_message_id'))
        await update.message.delete()
    except Exception: pass

    # Ahora que tenemos el nombre, pedimos el tipo de consulta
    await update.effective_chat.send_message(
        text="👍 ¡Gracias! Ahora, por favor, indica qué tipo de consulta solicitas:",
        reply_markup=keyboards.get_consultation_type_keyboard()
    )
    return SELECTING_CONSULTATION_TYPE



'''
async def handle_ever_pregnant(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    has_been_pregnant = query.data.endswith('_yes')
    context.user_data['booking_has_been_pregnant'] = has_been_pregnant

    text = "Entendido. Ahora, por favor, selecciona el motivo de esta visita:"
    reason_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🩺 Control Ginecológico", callback_data="book_reason_Control Ginecológico")],
        [InlineKeyboardButton("😖 Dolor pélvico", callback_data="book_reason_Dolor pélvico")],
        [InlineKeyboardButton("🩸 Sangrado", callback_data="book_reason_Sangrado")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="book_cancel")]
    ])
    await query.edit_message_text(text, reply_markup=reason_keyboard)
    return AWAITING_RECURRENT_REASON'''

async def handle_ever_pregnant(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Guarda si la paciente ha estado embarazada previamente (en un flujo ginecológico)
    y luego pregunta el motivo de la consulta.
    """
    query = update.callback_query
    await query.answer()

    # Guardamos la respuesta (True si el callback_data termina en '_yes')
    has_been_pregnant = query.data.endswith('_yes')
    context.user_data['booking_has_been_pregnant'] = has_been_pregnant

    # A continuación, siempre preguntamos el motivo de la visita.
    text = "Entendido. Ahora, por favor, selecciona el motivo de esta visita:"

    # Construimos el teclado para los motivos de consulta
    reason_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🩺 Control Ginecológico", callback_data="book_reason_control")],
        [InlineKeyboardButton("😖 Dolor pélvico", callback_data="book_reason_pain")],
        [InlineKeyboardButton("🩸 Sangrado", callback_data="book_reason_bleeding")],

        [InlineKeyboardButton("❌ Cancelar", callback_data="book_cancel")]
    ])

    # Editamos el mensaje actual para mostrar la nueva pregunta y teclado
    await query.edit_message_text(text, reply_markup=reason_keyboard)

    # Devolvemos el estado que espera por la selección del motivo
    return SELECTING_LOCATION

async def handle_first_pregnancy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Guarda si es el primer embarazo (en un flujo prenatal)
    y luego pregunta el motivo de la consulta.
    """
    query = update.callback_query
    await query.answer()

    is_first = query.data.endswith('_yes')
    context.user_data['booking_is_first_pregnancy'] = is_first

    text = "Gracias. Ahora, selecciona el motivo de tu consulta prenatal:"
    reason_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🩺 Control Prenatal", callback_data="book_reason_Control Prenatal")],
        [InlineKeyboardButton("😟 Dolor Pélvico", callback_data="book_reason_Dolor pélvico")],
        [InlineKeyboardButton("🩸 Sangrado", callback_data="book_reason_Sangrado")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="book_cancel")]
    ])
    await query.edit_message_text(text, reply_markup=reason_keyboard)
    # Retornar AWAITING_REASON para que el ConversationHandler maneje la selección del motivo
    # Después de seleccionar el motivo, el flujo continúa con SELECTING_LOCATION
    return AWAITING_REASON

# Función auxiliar para mostrar la confirmación (para no repetir código)
async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ud = context.user_data

    # Construimos el texto de confirmación (igual para todos)
    summary_text = (
        "📝 <b>Confirma los datos de tu cita:</b>\n\n"
        f"👤 <b>Paciente:</b> {escape_html(ud['booking_name'])}\n"
        f"🎯 <b>Tipo de Consulta:</b> {escape_html(ud['booking_consultation_type'])}\n"
        f"🗓️ <b>Fecha:</b> {ud['booking_date']}\n"
        f"⏰ <b>Hora:</b> {ud['booking_time']}\n"
        f"📍 <b>Ubicación:</b> {escape_html(ud['booking_location_name'])}"
    )

    # Siempre mostrar el motivo si existe
    if ud.get('booking_reason'):
        summary_text += f"\n🎯 <b>Motivo:</b> {escape_html(ud['booking_reason'])}"

    # Determinamos cómo mostrar el mensaje según el contexto
    if update.callback_query:
        # Venimos de handle_time (recurrentes)
        await update.callback_query.edit_message_text(
            text=summary_text,
            reply_markup=keyboards.get_confirmation_keyboard(),
            parse_mode=ParseMode.HTML
        )
    elif update.message:
        # Venimos de handle_name (nuevos)
        await update.effective_chat.send_message(
            text=summary_text,
            reply_markup=keyboards.get_confirmation_keyboard(),
            parse_mode=ParseMode.HTML
        )

    return CONFIRMING


async def confirm_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    ud = context.user_data
    doctor_id = ud.get('booking_doctor_id')
    user_id = update.effective_user.id

    if not doctor_id:
        await query.edit_message_text(
            "❌ Error: No se encontró el médico asignado.",
            reply_markup=keyboards.get_back_to_main_menu_keyboard()
        )
        return ConversationHandler.END

    consultation_type = ud.get('booking_consultation_type', 'Ginecológica')
    is_first_pregnancy = ud.get('booking_is_first_pregnancy')
    has_been_pregnant = ud.get('booking_has_been_pregnant')
    pregnancy_status = is_first_pregnancy if is_first_pregnancy is not None else (not has_been_pregnant if has_been_pregnant is not None else None)
    reason = ud.get('booking_reason') or consultation_type

    new_appointment_id = await _create_appointment(
        doctor_id=doctor_id,
        user_id=user_id,
        user_name=ud['booking_name'],
        fecha=ud['booking_date'],
        hora=ud['booking_time'],
        ubicacion=ud['booking_location_name'],
        status='pending',
        reason=reason,
        consultation_type=consultation_type,
        is_first_pregnancy=pregnancy_status,
        has_been_pregnant=has_been_pregnant
    )

    if new_appointment_id:
        logger.info(f"Cita #{new_appointment_id} guardada con éxito para {ud['booking_name']}.")

        try:
            doctor_telegram_id = await _get_doctor_telegram_id(doctor_id)
            if doctor_telegram_id:
                user = update.effective_user
                user_info = user.full_name + (f" (@{user.username})" if user.username else "")
                notification_text = (
                    f"🗓️ <b>¡Nueva Cita Agendada!</b>\n\n"
                    + f"👤 <b>Paciente:</b> {escape_html(ud['booking_name'])}\n"
                    + f"<i>(Usuario: {escape_html(user_info)})</i>\n\n"
                    + f"<b>Detalles de la Cita:</b>\n"
                    + f"<blockquote>"
                    + f"🎯 <b>Tipo:</b> {escape_html(consultation_type)}\n"
                    + f"🗓️ <b>Fecha:</b> {ud['booking_date']}\n"
                    + f"⏰ <b>Hora:</b> {ud['booking_time']}\n"
                    + f"📍 <b>Ubicación:</b> {escape_html(ud['booking_location_name'])}"
                    + f"</blockquote>"
                )

                # 2. Definimos el teclado por separado
                notification_keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("⏰ Recuérdame ", callback_data=f"appt_remind_later_{new_appointment_id}"),
                        InlineKeyboardButton("🗑️ Descartar", callback_data=f"appt_dismiss_{new_appointment_id}")
                    ]
                ])

                # 3. Enviamos el mensaje pasando las variables
                await context.bot.send_message(
                    chat_id=doctor_telegram_id,
                    text=notification_text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=notification_keyboard
                )
        except Exception as e:
            logger.error(f"FALLO al enviar notificación de nueva cita al admin: {e}", exc_info=True)

        success_text = (
            f"✅ <b>¡Tu solicitud de cita ha sido enviada con éxito!</b>\n\n"
            f"<b>Resumen:</b>\n"
            f"🎯 <b>Tipo:</b> {escape_html(consultation_type)}\n"
            f"🗓️ {ud['booking_date']} a las {ud['booking_time']}\n"
            f"📍 {escape_html(ud['booking_location_name'])}\n\n"
            "Recibirás una notificación tan pronto como tu médico confirme la cita. ¡Gracias!"
        )

        reply_markup = keyboards.get_finish_booking_keyboard()
        # --- FIN DE LA CORRECCIÓN ---

        await query.edit_message_text(
            success_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        return FINAL_STATE
    else:
        # Para el mensaje de error, podemos seguir usando la genérica si queremos
        await query.edit_message_text(
            "❌ Ha ocurrido un error al guardar tu cita. Por favor, inténtalo de nuevo.",
            reply_markup=keyboards.get_back_to_main_menu_keyboard() # O la nueva, ambas funcionan aquí
        )
        context.user_data.clear()
        return ConversationHandler.END
'''
async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Función universal para salir o finalizar el flujo y mostrar el menú principal.
    Limpia la conversación y muestra un menú nuevo.
    """
    query = update.callback_query
    if query:
        await query.answer()

        # Si el mensaje aún existe, lo editamos para dar feedback al usuario
        if query.message:
            try:
                # Si el callback es 'main_menu', significa que es una cancelación
                if query.data == 'main_menu':
                    await query.edit_message_text("Operación cancelada. Volviendo al menú principal...")
                    await asyncio.sleep(1.5)
                # Si no, es el final del flujo normal y el mensaje ya es de éxito,
                # por lo que no necesita edición, solo será borrado.
            except BadRequest as e:
                # Ignorar error si el mensaje ya no existe
                if "message to edit not found" not in str(e).lower():
                    logger.warning(f"Error al editar mensaje en back_to_main_menu: {e}")

    # Limpiamos los datos de la conversación de citas
    context.user_data.clear()

    # Llamamos a la función del menú principal que ya se encarga de limpiar
    # el mensaje anterior y enviar uno nuevo.
    await show_main_menu_and_cleanup(update, context)

    return ConversationHandler.END'''
'''
async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query:
        await query.answer()
    context.user_data.clear()
    await show_main_menu_and_cleanup(update, context) # Llama a la función del menú
    return ConversationHandler.END # Termina la conversación'''

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Finaliza la conversación de agendamiento y vuelve al menú principal del paciente.
    """
    query = update.callback_query
    if query:
        await query.answer()

    doctor_id = await _get_doctor_id_from_context(update, context)
    context.user_data.clear()

    if doctor_id:
        await patient_main_menu(update, context, doctor_id)
    else:
        if query and query.message:
            await query.edit_message_text(
                "❌ No tienes un médico asignado.",
                parse_mode="HTML"
            )

    return ConversationHandler.END

async def back_to_locations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Devuelve al usuario a la pantalla de selección de ubicación.
    Usado por el botón 'Modificar' en la pantalla de confirmación.
    """
    query = update.callback_query
    await query.answer()

    doctor_id = context.user_data.get('booking_doctor_id')
    locations_keyboard = await keyboards.get_locations_keyboard(doctor_id)

    await query.edit_message_text(
        "📍 Por favor, selecciona la ubicación:",
        reply_markup=locations_keyboard
    )

    # Devuelve el estado correspondiente a la selección de ubicación
    return SELECTING_LOCATION

async def cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Proceso de agendamiento cancelado.")
    await asyncio.sleep(1.5)
    
    doctor_id = await _get_doctor_id_from_context(update, context)
    context.user_data.clear()
    
    if doctor_id:
        await patient_main_menu(update, context, doctor_id)
    
    return ConversationHandler.END

async def dismiss_notification(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejador para el botón 'Descartar Notificación'. Borra el mensaje y muestra el menú principal."""
    query = update.callback_query
    await query.answer()

    try:
        await query.message.delete()
    except Exception as e:
        logger.warning(f"No se pudo borrar el mensaje de notificación: {e}")

    # Mostrar menú principal del paciente
    doctor_id = await _get_doctor_id_from_context(update, context)
    if doctor_id:
        await patient_main_menu(update, context, doctor_id)

async def exit_booking_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Finaliza la conversación de agendamiento de forma segura, editando el mensaje
    y luego llamando a la función del menú principal para enviar uno nuevo.
    """
    query = update.callback_query
    if query:
        await query.answer()
        try:
            await query.edit_message_text("Operación cancelada. Volviendo al menú principal...")
        except BadRequest as e:
            if "message is not modified" not in str(e).lower():
                logger.warning(f"No se pudo editar mensaje al salir del flujo de citas: {e}")

    doctor_id = await _get_doctor_id_from_context(update, context)
    context.user_data.clear()

    if doctor_id:
        await patient_main_menu(update, context, doctor_id)

    return ConversationHandler.END

def register(app: Application):
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_booking, pattern='^patient_book_appointment$')],
        states={
            AWAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],

            SELECTING_CONSULTATION_TYPE: [
                CallbackQueryHandler(handle_consultation_type, pattern='^book_consult_type_')
            ],

            AWAITING_PREGNANCY_INFO: [
                CallbackQueryHandler(handle_pregnancy_info, pattern='^book_(first|ever)_preg_')
            ],

            AWAITING_REASON: [
                CallbackQueryHandler(handle_reason, pattern='^book_reason_')
            ],

            SELECTING_LOCATION: [CallbackQueryHandler(handle_location, pattern='^book_loc_')],

            SELECTING_DATE: [
                CallbackQueryHandler(calendar_handler_booking, pattern='^book_cal_'),
                CallbackQueryHandler(back_to_locations, pattern='^book_back_to_locations$')
            ],

            SELECTING_TIME: [
                CallbackQueryHandler(handle_time, pattern='^book_time_'),
                CallbackQueryHandler(calendar_handler_booking, pattern='^book_back_to_calendar$')
            ],

            CONFIRMING: [
                CallbackQueryHandler(confirm_appointment, pattern='^book_confirm_yes$'),
                CallbackQueryHandler(back_to_locations, pattern='^book_back_to_locations$')
            ],

            FINAL_STATE: [CallbackQueryHandler(back_to_main_menu, pattern='^book_back_to_main_menu$')]
        },
        fallbacks=[CallbackQueryHandler(back_to_main_menu, pattern='^main_menu$'),
            # --- FIN DE LÍNEAS AÑADIDAS ---
            CallbackQueryHandler(cancel_booking, pattern='^book_cancel$')],
        per_message=False,
        allow_reentry=True
    )
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(dismiss_notification, pattern='^dismiss_notification$'))