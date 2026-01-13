from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import html

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
    keyboard.append([InlineKeyboardButton("🏠 Menú Principal", callback_data="main_menu")])
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
    # TODO: Implementar obtención de slots ocupados para reagendamiento
    available_slots = POSSIBLE_SLOTS  # Por ahora, todas disponibles

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