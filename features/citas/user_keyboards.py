# AgendarCita/user_keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
from config import DB_PATH
from database.session import get_session
from database.repositories.appointment_repository import SlotRepository, AppointmentRepository
from database import locations_db, connection
from sqlalchemy import select
from database.models.appointment import Appointment, Slot

async def _doctor_id_to_bot_id(doctor_id: int) -> int | None:
    """Convierte doctor_id a bot_id."""
    conn = await connection.get_db_connection()
    bot_id = None
    if conn:
        try:
            async with conn.execute("SELECT telegram_id FROM doctors WHERE id = ?", (doctor_id,)) as cursor:
                doctor_row = await cursor.fetchone()
                if doctor_row:
                    telegram_id = doctor_row['telegram_id']
                    async with conn.execute(
                        "SELECT id FROM bots WHERE admin_user_id = ? AND is_active = 1",
                        (telegram_id,)
                    ) as bot_cursor:
                        bot_row = await bot_cursor.fetchone()
                        if bot_row:
                            bot_id = bot_row['id']
        finally:
            await conn.close()
    return bot_id


def get_finish_booking_keyboard():
    """
    Genera un teclado para el final del flujo de agendamiento,
    usando un callback que la conversación de citas pueda manejar.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data="book_back_to_main_menu")]
    ])


def get_ever_pregnant_keyboard():
    """Genera un teclado para preguntar si ha estado embarazada alguna vez."""
    keyboard = [
        [InlineKeyboardButton("✅ Sí, he estado antes", callback_data="book_ever_preg_yes")],
        [InlineKeyboardButton("🚫 No, nunca", callback_data="book_ever_preg_no")],
        [InlineKeyboardButton("🏠 Menú Principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_first_pregnancy_keyboard():
    """Genera un teclado para preguntar si es el primer embarazo."""
    keyboard = [
        [InlineKeyboardButton("✅ Sí, es mi primero", callback_data="book_first_preg_yes")],
        [InlineKeyboardButton("🚫 No, he tenido otros", callback_data="book_first_preg_no")],
        [InlineKeyboardButton("🏠 Menú Principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_consultation_type_keyboard():
    """Genera el teclado para seleccionar el tipo de consulta."""
    keyboard = [
        [InlineKeyboardButton("🩺 Ginecológica", callback_data="book_consult_type_Ginecológica")],
        [InlineKeyboardButton("🤰 Prenatal", callback_data="book_consult_type_Prenatal")],
        [InlineKeyboardButton("🏠 Menú Principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_locations_keyboard(doctor_id: int):
    """Genera un teclado con las ubicaciones disponibles (multi-tenant)."""
    bot_id = await _doctor_id_to_bot_id(doctor_id)
    if not bot_id:
        bot_id = doctor_id

    locations = await locations_db.get_locations_for_bot(bot_id)
    keyboard = []
    if not locations:
        keyboard.append([InlineKeyboardButton("📍 Ubicación no especificada", callback_data="book_loc_-1")])
    else:
        for loc in locations:
            title = loc.get('name', 'Ubicación')
            keyboard.append([InlineKeyboardButton(f"📍 {title}", callback_data=f"book_loc_{loc['id']}")])

    keyboard.append([
        InlineKeyboardButton("❌ Cancelar", callback_data="book_cancel"),
        InlineKeyboardButton("🏠 ", callback_data="patient_main_menu")
    ])
    return InlineKeyboardMarkup(keyboard)

async def get_available_time_slots_keyboard(doctor_id: int, selected_date: str):
    """Genera un teclado con las horas disponibles (multi-tenant)."""
    POSSIBLE_SLOTS = [
        "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
        "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"
    ]

    # Obtener slots ocupados para este doctor y día
    occupied_slots = []
    try:
        dt = datetime.strptime(selected_date, "%Y-%m-%d")
        start_ts = int(dt.timestamp())
        end_ts = start_ts + 86400

        async with get_session() as session:
            result = await session.execute(
                select(Slot.start_ts)
                .join(Appointment, Slot.id == Appointment.slot_id)
                .where(
                    Slot.doctor_id == doctor_id,
                    Slot.start_ts >= start_ts,
                    Slot.start_ts < end_ts
                )
            )
            occupied = result.scalars().all()

            for start_ts_value in occupied:
                dt_slot = datetime.fromtimestamp(start_ts_value)
                occupied_slots.append(dt_slot.strftime("%H:%M"))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error al obtener slots ocupados: {e}")

    available_slots = [slot for slot in POSSIBLE_SLOTS if slot not in occupied_slots]

    keyboard = []
    if not available_slots:
        keyboard.append([InlineKeyboardButton("No hay horas disponibles para este día", callback_data="ignore")])
    else:
        for i in range(0, len(available_slots), 2):
            row = [InlineKeyboardButton(slot, callback_data=f"book_time_{slot}") for slot in available_slots[i:i+2]]
            keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("🔙 Elegir otra fecha", callback_data="book_back_to_calendar"),
        InlineKeyboardButton("❌ Cancelar", callback_data="book_cancel")
    ])
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard():
    """Genera el teclado para la pantalla de confirmación."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirmar Cita", callback_data="book_confirm_yes"),
            InlineKeyboardButton("✏️ Modificar", callback_data="book_back_to_locations") # Vuelve al inicio del flujo
        ]
    ])

def get_back_to_main_menu_keyboard():
    """Genera un teclado simple para volver al menú principal después de agendar."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 ", callback_data="book_back_to_main_menu")]
    ])

def get_start_preconsultation_keyboard(appointment_id: int) -> InlineKeyboardMarkup:
    """Crea un teclado con un callback_data que incluye el ID de la cita."""
    keyboard = [[
        InlineKeyboardButton("📝 Llenar Preconsulta Ahora", callback_data=f"start_preconsultation_{appointment_id}")
    ]]
    return InlineKeyboardMarkup(keyboard)