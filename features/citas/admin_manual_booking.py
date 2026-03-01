import logging
import html
from datetime import date, datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, Application
from telegram.constants import ParseMode
from database.session import get_session
from database.repositories.appointment_repository import AppointmentRepository, SlotRepository
from database import locations_db
from features.citas.admin_calendar import CustomCalendar
from features.citas.admin_keyboards import get_reschedule_time_slots_keyboard
from features.citas.user_keyboards import get_locations_keyboard
from features.citas.admin_handlers import _get_doctor_id, render_citas_panel

logger = logging.getLogger(__name__)

SELECTING_LOCATION = 0
ENTERING_NAME = 1
ENTERING_REASON = 2
SELECTING_DATE = 3
SELECTING_TIME = 4
CONFIRMING = 5

def escape_html(text: str) -> str:
    return html.escape(str(text))

async def start_manual_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    doctor_id = await _get_doctor_id(update)
    if not doctor_id:
        await query.message.reply_text("⛔ Solo administradores pueden agregar citas.")
        return ConversationHandler.END
        
    context.user_data['manual_booking_doctor_id'] = doctor_id
    
    locations_keyboard = await get_locations_keyboard(doctor_id)

    # Reconstruir el teclado porque InlineKeyboardButton es inmutabble en python-telegram-bot v20+
    new_keyboard = []
    for row in locations_keyboard.inline_keyboard:
        new_row = []
        for btn in row:
            if btn.callback_data and btn.callback_data.startswith("book_loc_"):
                new_callback = btn.callback_data.replace("book_loc_", "ad_book_loc_")
                new_row.append(InlineKeyboardButton(text=btn.text, callback_data=new_callback))
            elif btn.callback_data and btn.callback_data == "book_cancel":
                new_row.append(InlineKeyboardButton(text="❌ Cancelar", callback_data="ad_book_cancel"))
            elif btn.callback_data and btn.callback_data == "patient_main_menu":
                pass # eliminar el botón al menu del paciente
            else:
                new_row.append(btn)
        if new_row:
            new_keyboard.append(new_row)
                
    await query.message.edit_text(
        "📍 **Agregar Cita Manual**\nPrimero, selecciona la **ubicación** para este bloque:",
        reply_markup=InlineKeyboardMarkup(new_keyboard), parse_mode='Markdown'
    )
    return SELECTING_LOCATION

async def handle_location_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    location_id = int(parts[3])
    context.user_data['manual_booking_location_id'] = location_id

    location_name = "Ubicación no especificada"
    if location_id >= 0:
        details = await locations_db.get_location_details(location_id)
        if details and details.get('name'):
            location_name = details['name']
    context.user_data['manual_booking_location_name'] = location_name

    await query.message.edit_text(
        f"📍 Ubicación: **{location_name}**\n\n👤 Ahora, por favor, ingresa el **nombre completo del paciente** o título del bloqueo:",
        parse_mode='Markdown'
    )
    return ENTERING_NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data['manual_booking_patient_name'] = name
    
    await update.message.reply_text(
        f"👤 Nombre: **{name}**\n\n🎯 ¿Cuál es el motivo de la cita?",
        parse_mode='Markdown'
    )
    return ENTERING_REASON

async def handle_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reason = update.message.text.strip()
    context.user_data['manual_booking_reason'] = reason

    calendar = CustomCalendar().create_admin_booking_calendar()
    
    await update.message.reply_text(
        f"🎯 Motivo: **{reason}**\n\n📅 Excelente. Selecciona la **fecha** para la cita:",
        reply_markup=calendar, parse_mode='Markdown'
    )
    return SELECTING_DATE

async def admin_calendar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("ad_book_cal_nav_"):
        year, month = map(int, data.split('_')[-1].split('-'))
        calendar = CustomCalendar().create_admin_booking_calendar(year=year, month=month)
        await query.message.edit_reply_markup(reply_markup=calendar)
        return SELECTING_DATE
        
    if data.startswith("ad_book_cal_day_"):
        selected_date = CustomCalendar().process_selection(data)
        if not selected_date:
            return SELECTING_DATE
            
        context.user_data["manual_booking_date"] = selected_date.isoformat()
        doctor_id = context.user_data.get('manual_booking_doctor_id')
        
        times_keyboard = await get_reschedule_time_slots_keyboard(
            doctor_id, selected_date.isoformat(), 0, "manual", 0, "admin"
        )
        
        # Reconstruir el teclado de horas disponibles para no mutar los InlineKeyboardButton
        new_times_keyboard = []
        for row in times_keyboard.inline_keyboard:
            new_row = []
            for btn in row:
                if btn.callback_data and btn.callback_data.startswith("reschedule_back_to_calendar"):
                    new_row.append(InlineKeyboardButton(text=btn.text, callback_data="ad_book_back_to_calendar"))
                elif btn.callback_data and btn.callback_data.startswith("reschedule_time_"):
                    time_slot = btn.callback_data.split('_')[2]
                    new_row.append(InlineKeyboardButton(text=btn.text, callback_data=f"ad_book_time_{time_slot}"))
                else:
                    new_row.append(btn)
            new_times_keyboard.append(new_row)
                    
        await query.message.edit_text(
            f"📅 Fecha seleccionada: **{selected_date.strftime('%d/%m/%Y')}**\n\n⏰ Selecciona una **hora** disponible:",
            reply_markup=InlineKeyboardMarkup(new_times_keyboard),
            parse_mode='Markdown'
        )
        return SELECTING_TIME
    
    return SELECTING_DATE

async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "ad_book_back_to_calendar":
        calendar = CustomCalendar().create_admin_booking_calendar()
        await query.message.edit_text("📅 Selecciona la fecha:", reply_markup=calendar)
        return SELECTING_DATE
        
    if not data.startswith("ad_book_time_"):
        return SELECTING_TIME
        
    time_slot = data.split('_')[-1]
    context.user_data['manual_booking_time'] = time_slot
    
    ud = context.user_data
    summary_text = (
        "📝 <b>Confirma los datos de la cita manual:</b>\n\n"
        f"👤 <b>Paciente:</b> {escape_html(ud.get('manual_booking_patient_name'))}\n"
        f"🎯 <b>Motivo:</b> {escape_html(ud.get('manual_booking_reason'))}\n"
        f"🗓️ <b>Fecha:</b> {ud.get('manual_booking_date')}\n"
        f"⏰ <b>Hora:</b> {ud.get('manual_booking_time')}\n"
        f"📍 <b>Ubicación:</b> {escape_html(ud.get('manual_booking_location_name'))}"
    )

    confirm_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirmar Cita", callback_data="ad_book_confirm_yes"),
            InlineKeyboardButton("❌ Cancelar", callback_data="ad_book_cancel")
        ]
    ])
    
    await query.message.edit_text(
        text=summary_text,
        reply_markup=confirm_keyboard,
        parse_mode=ParseMode.HTML
    )
    return CONFIRMING

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    ud = context.user_data
    doctor_id = ud.get('manual_booking_doctor_id')
    selected_date = ud.get('manual_booking_date')
    selected_time = ud.get('manual_booking_time')
    patient_name = ud.get('manual_booking_patient_name', 'Paciente Manual')
    reason = ud.get('manual_booking_reason', 'Cita Manual')
    location = ud.get('manual_booking_location_name', 'Ubicación no especificada')
    
    if not doctor_id or not selected_date or not selected_time:
        await query.message.reply_text("❌ Error de sesión al confirmar. Por favor intenta de nuevo.")
        return ConversationHandler.END
        
    try:
        dt = datetime.strptime(f"{selected_date} {selected_time}", "%Y-%m-%d %H:%M")
        start_ts = int(dt.timestamp())
    except Exception as e:
        logger.error(f"Error parsing date/time for manual booking: {e}")
        await query.message.reply_text("❌ Error con la fecha u hora.")
        return ConversationHandler.END
        
    async with get_session() as session:
        slot_repo = SlotRepository(session)
        appt_repo = AppointmentRepository(session)
        
        # 1. Crear el slot manual
        slot = await slot_repo.add_slot(
            doctor_id=doctor_id,
            start_ts=start_ts,
            duration_min=30,
            note=f"Bloqueo Manual: {reason}"
        )
        
        # 2. Reservar el appointment forzadamente
        success = await appt_repo.book_slot(
            doctor_id=doctor_id,
            slot_id=slot.id,
            patient_telegram_id=doctor_id,  # Dummy ID (Admin sí mismo)
            patient_name=patient_name,
            consultation_type="Cita Manual",
            reason=reason,
            location=location,
            status="confirmed"
        )
        
        if success:
             await query.message.edit_text(f"✅ ¡Cita manual de **{patient_name}** por **{reason}** registrada con éxito!\n\n📍 Ubicación: **{location}**\nSe ha bloqueado el horario: **{selected_date} {selected_time}**", parse_mode='Markdown')
        else:
            await query.message.edit_text("❌ Hubo un error al registrar la cita manual en la base de datos.")

    # Clean up states
    ud.pop('manual_booking_doctor_id', None)
    ud.pop('manual_booking_location_id', None)
    ud.pop('manual_booking_location_name', None)
    ud.pop('manual_booking_patient_name', None)
    ud.pop('manual_booking_reason', None)
    ud.pop('manual_booking_date', None)
    ud.pop('manual_booking_time', None)
    
    # Send another message with panel instead of editing again
    await render_citas_panel(update, context, 'list', filter_type='all-pending', page_index=0)
    
    return ConversationHandler.END

async def cancel_manual_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Cleanup config
    context.user_data.pop('manual_booking_doctor_id', None)
    context.user_data.pop('manual_booking_location_id', None)
    context.user_data.pop('manual_booking_location_name', None)
    context.user_data.pop('manual_booking_patient_name', None)
    context.user_data.pop('manual_booking_reason', None)
    context.user_data.pop('manual_booking_date', None)
    context.user_data.pop('manual_booking_time', None)
    
    await render_citas_panel(update, context, 'list', filter_type='all-pending', page_index=0)
    return ConversationHandler.END

def register(app: Application):
    add_manual_appt_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_manual_booking, pattern="^citas_admin_add_manual$")],
        states={
            SELECTING_LOCATION: [
                CallbackQueryHandler(handle_location_selection, pattern="^ad_book_loc_")
            ],
            ENTERING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)
            ],
            ENTERING_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reason)
            ],
            SELECTING_DATE: [
                CallbackQueryHandler(admin_calendar_handler, pattern="^ad_book_cal_"),
                CallbackQueryHandler(cancel_manual_booking, pattern="^ad_book_cancel$")
            ],
            SELECTING_TIME: [
                CallbackQueryHandler(handle_time_selection, pattern="^ad_book_(time_|back_to_)")
            ],
            CONFIRMING: [
                CallbackQueryHandler(handle_confirmation, pattern="^ad_book_confirm_yes$")
            ]
        },
        fallbacks=[CallbackQueryHandler(cancel_manual_booking, pattern="^ad_book_cancel$")],
        name="add_manual_appt_conv",
        persistent=True,
        allow_reentry=True
    )
    app.add_handler(add_manual_appt_conv)
