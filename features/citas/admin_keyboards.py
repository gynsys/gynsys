from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import html
from datetime import datetime
from sqlalchemy import select
from database.session import get_session
from database.models import Slot, Appointment

def escape_html(text: str) -> str:
    return html.escape(str(text))

def get_citas_list_keyboard(citas_paginadas: list, page_index: int, total_citas: int, filter_type: str):
    keyboard = []
    citas_por_pagina = 5
    for cita in citas_paginadas:
        callback_data = f"citas_detail_{cita['id']}_{filter_type}_{page_index}"
        label = cita.get("descripcion") or f"{cita['fecha']} {cita['hora']} - {escape_html(cita['user_name'])}"
        keyboard.append([
            InlineKeyboardButton(
                label,
                callback_data=callback_data
            )
        ])
    page_buttons = []
    total_paginas = (total_citas + citas_por_pagina - 1) // citas_por_pagina
    if page_index > 0:
        page_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data=f"citas_view_{filter_type}_{page_index-1}"))
    if page_index < total_paginas - 1:
        page_buttons.append(InlineKeyboardButton("Siguiente ➡️", callback_data=f"citas_view_{filter_type}_{page_index+1}"))
    if page_buttons:
        keyboard.append(page_buttons)
    # Split the row logic
    keyboard.append([
        InlineKeyboardButton("🏠", callback_data="main_menu"),
        InlineKeyboardButton("➕ Agregar cita", callback_data="citas_admin_add_manual")
    ])
    return InlineKeyboardMarkup(keyboard)

def get_cita_detail_keyboard(cita_id: int, filter_type: str, page_index: int):
    keyboard = [
        [
            InlineKeyboardButton("✅ Completada", callback_data=f"citas_action_complete_{cita_id}_{filter_type}_{page_index}")

            #InlineKeyboardButton("👍 Confirmar", callback_data=f"citas_action_confirm_{cita_id}_{filter_type}_{page_index}")
        ],
        [
            InlineKeyboardButton("❌ Cancelar Cita", callback_data=f"citas_action_cancel_{cita_id}_{filter_type}_{page_index}"),
            InlineKeyboardButton("🔄 Reagendar", callback_data=f"citas_action_reschedule_{cita_id}_{filter_type}_{page_index}")
        ],
        [
            InlineKeyboardButton("🗑️ Eliminar Registro", callback_data=f"citas_action_delete_{cita_id}_{filter_type}_{page_index}")
        ],
        [
            InlineKeyboardButton("« Volver a la Lista", callback_data=f"citas_view_{filter_type}_{page_index}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_cita_confirm_action_keyboard(action: str, cita_id: int, filter_type: str, page_index: int):
    action_details = {'cancel': {'text': 'CANCELAR', 'emoji': '❌'}, 'delete': {'text': 'BORRAR', 'emoji': '🗑️'}}
    details = action_details.get(action, {'text': action.upper(), 'emoji': '🚨'})
    callback_base = f"citas_confirm_{action}_{cita_id}_{filter_type}_{page_index}"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"{details['emoji']} SÍ, {details['text']}", callback_data=callback_base),
            InlineKeyboardButton("⬅️ No, Regresar", callback_data=f"citas_detail_{cita_id}_{filter_type}_{page_index}")
        ]
    ])

async def get_reschedule_time_slots_keyboard(doctor_id: int, selected_date: str, cita_id: int, filter_type: str, page_index: int, origin: str):
    """
    Genera un teclado con las horas disponibles para REAGENDAR (multi-tenant).
    """
    POSSIBLE_SLOTS = [
        "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
        "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"
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
                    Slot.start_ts < end_ts,
                    Appointment.status != 'cancelled'
                )
            )
            occupied = result.scalars().all()

            for start_ts_value in occupied:
                dt_slot = datetime.fromtimestamp(start_ts_value)
                occupied_slots.append(dt_slot.strftime("%H:%M"))
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error al obtener slots ocupados admin: {e}")

    available_slots = [slot for slot in POSSIBLE_SLOTS if slot not in occupied_slots]

    keyboard = []
    if not available_slots:
        keyboard.append([InlineKeyboardButton("No hay horas disponibles para este día", callback_data="ignore")])
    else:
        for i in range(0, len(available_slots), 2):
            row = [InlineKeyboardButton(slot, callback_data=f"reschedule_time_{slot}_{cita_id}_{filter_type}_{page_index}_{origin}") for slot in available_slots[i:i+2]]
            keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("🔙 Elegir otra fecha", callback_data=f"reschedule_back_to_calendar_{cita_id}_{filter_type}_{page_index}_{origin}"),
    ])
    return InlineKeyboardMarkup(keyboard)