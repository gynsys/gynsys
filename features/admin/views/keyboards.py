"""
Construcción de teclados inline para el módulo admin.
Solo construcción de botones, sin lógica de negocio.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_doctors_management_keyboard():
    """
    Teclado para gestión de médicos (submenú)
    """
    keyboard = [
        [
            InlineKeyboardButton("➕ Agregar", callback_data="add_doctor"),
            InlineKeyboardButton("🗑️ Eliminar", callback_data="delete_doctor_menu")
        ],
        [
            InlineKeyboardButton("🔒 Restringir", callback_data="simple_restrict_menu"),
            InlineKeyboardButton("🔓 Permitir", callback_data="simple_permit_menu")
        ],
        [
            InlineKeyboardButton("🔧 Módulos Extras", callback_data="extra_modules_hub")
        ],
        [
            InlineKeyboardButton("🏠 ", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_main_keyboard():
    """
    Teclado para volver al menú principal
    """
    keyboard = [
        [InlineKeyboardButton("🏠 ", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_doctors_keyboard():
    """
    Teclado para volver al menú de médicos
    """
    keyboard = [
        [InlineKeyboardButton("👨‍⚕️ Volver ", callback_data="doctors_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_doctors_list_keyboard(doctors, page=0, total_pages=1):
    """
    Teclado para listar médicos con paginación.
    
    Args:
        doctors: Lista de tuplas (id, name, telegram_id)
        page: Página actual (0-indexed)
        total_pages: Total de páginas
    """
    keyboard = []
    for doctor in doctors:
        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ {doctor[1]}",
                callback_data=f"simple_delete_{doctor[0]}"
            )
        ])
    
    # Navegación
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"doctors_page_{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"doctors_page_{page + 1}"))
    if nav:
        keyboard.append(nav)
    
    keyboard.append([InlineKeyboardButton("👨‍⚕️ Volver", callback_data="doctors_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_delete_doctors_keyboard(doctors, page=0, total_pages=1):
    """
    Teclado para eliminar médicos con paginación.
    """
    keyboard = []
    for doctor in doctors:
        keyboard.append([
            InlineKeyboardButton(f"🗑️ {doctor[1]}", callback_data=f"simple_delete_{doctor[0]}")
        ])
    
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"delete_doctor_page_{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"delete_doctor_page_{page + 1}"))
    if nav:
        keyboard.append(nav)
    
    keyboard.append([InlineKeyboardButton("👨‍⚕️ Volver", callback_data="doctors_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_restrict_doctors_keyboard(doctors, page=0, total_pages=1):
    """
    Teclado para restringir médicos con paginación.
    """
    keyboard = [
        [InlineKeyboardButton(f"🔒 {doc[1]}", callback_data=f"simple_restrict_{doc[0]}")]
        for doc in doctors
    ]
    
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"simple_restrict_page_{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"simple_restrict_page_{page + 1}"))
    if nav:
        keyboard.append(nav)
    
    keyboard.append([InlineKeyboardButton("👨‍⚕️ Volver", callback_data="doctors_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_permit_doctors_keyboard(doctors, page=0, total_pages=1):
    """
    Teclado para permitir médicos con paginación.
    """
    keyboard = [
        [InlineKeyboardButton(f"🔓 {doc[1]}", callback_data=f"simple_permit_{doc[0]}")]
        for doc in doctors
    ]
    
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"simple_permit_page_{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"simple_permit_page_{page + 1}"))
    if nav:
        keyboard.append(nav)
    
    keyboard.append([InlineKeyboardButton("👨‍⚕️ Volver", callback_data="doctors_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_requests_list_keyboard(requests):
    """
    Teclado para listar solicitudes de médicos.
    
    Args:
        requests: Lista de diccionarios con 'id' y 'full_name'
    """
    keyboard = []
    for req in requests:
        keyboard.append([
            InlineKeyboardButton(f"📄 {req['full_name']}", callback_data=f"request_detail_{req['id']}")
        ])
    keyboard.append([InlineKeyboardButton("🏠", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)


def get_request_detail_keyboard(request_id):
    """
    Teclado para detalle de solicitud.
    
    Args:
        request_id: ID de la solicitud
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Aprobar", callback_data=f"request_approve_{request_id}"),
            InlineKeyboardButton("❌ Rechazar", callback_data=f"request_reject_{request_id}")
        ],
        [InlineKeyboardButton("↩️ Solicitudes", callback_data="requests_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

