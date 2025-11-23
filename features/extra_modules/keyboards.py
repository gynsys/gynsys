"""
Teclados para gestión de módulos extras
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_extra_modules_hub_keyboard():
    """Teclado principal del hub de módulos extras"""
    keyboard = [
        [InlineKeyboardButton("👨‍⚕️ Gestionar por Doctor", callback_data="extra_modules_by_doctor")],
        [InlineKeyboardButton("🔙 Volver", callback_data="doctors_menu")],
        [InlineKeyboardButton("🏠 Menú Principal", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_doctors_list_keyboard(doctors: list, page: int = 0, page_size: int = 7, return_to: str = "doctors_menu"):
    """Teclado con lista de doctores paginada"""
    keyboard = []
    
    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_doctors = doctors[start_idx:end_idx]
    
    for doctor in page_doctors:
        modules_text = f" ({len(doctor['modules'])} módulos)" if doctor['modules'] else " (0 módulos)"
        keyboard.append([
            InlineKeyboardButton(
                f"👨‍⚕️ {doctor['name']}{modules_text}",
                callback_data=f"extra_modules_doctor_{doctor['doctor_id']}"
            )
        ])
    
    # Navegación - usar el callback correcto según el return_to
    nav_row = []
    if page > 0:
        if return_to == "doctors_menu":
            nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"doctors_modules_page_{page - 1}"))
        else:
            nav_row.append(InlineKeyboardButton("⬅️", callback_data=f"extra_modules_page_{page - 1}"))
    if end_idx < len(doctors):
        if return_to == "doctors_menu":
            nav_row.append(InlineKeyboardButton("➡️", callback_data=f"doctors_modules_page_{page + 1}"))
        else:
            nav_row.append(InlineKeyboardButton("➡️", callback_data=f"extra_modules_page_{page + 1}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    # Botón de volver según el contexto
    if return_to == "doctors_menu":
        keyboard.append([InlineKeyboardButton("🏠 Menú Principal", callback_data="main_menu")])
    else:
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="extra_modules_hub")])
    
    return InlineKeyboardMarkup(keyboard)

def get_doctor_modules_keyboard(doctor_id: int, doctor_name: str, available_modules: list, active_modules: list, return_to: str = "doctors_menu"):
    """Teclado para gestionar módulos de un doctor específico"""
    keyboard = []
    
    for module in available_modules:
        module_name = module['name']
        is_active = module_name in active_modules
        status_emoji = "✅" if is_active else "❌"
        button_text = f"{status_emoji} {module['display_name']}"
        
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"extra_modules_toggle_{doctor_id}_{module_name}"
            )
        ])
    
    # Botón de volver según el contexto
    if return_to == "doctors_menu":
        keyboard.append([InlineKeyboardButton("🔙 Volver a Lista de Médicos", callback_data="doctors_menu")])
    else:
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="extra_modules_by_doctor")])
    
    return InlineKeyboardMarkup(keyboard)

