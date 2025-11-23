from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_contact_menu_keyboard():
    """Teclado para que el médico configure su información de contacto."""
    # Versión mínima: solo botón para volver al inicio del panel del doctor
    keyboard = [
        [InlineKeyboardButton("🏠 Inicio", callback_data="doctor_main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_edit_keyboard():
    """Teclado para cancelar la edición de un campo."""
    keyboard = [
        [InlineKeyboardButton("❌ Cancelar", callback_data="contact_cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_contact_menu_keyboard():
    """Teclado para volver al menú de contacto después de una vista previa."""
    keyboard = [
        [InlineKeyboardButton("↩️ Volver a Contacto", callback_data="contacto_menu")],
        [InlineKeyboardButton("🏠 Menú", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_patient_contact_keyboard():
    """Teclado para pacientes cuando ven el contacto del doctor."""
    keyboard = [
        [InlineKeyboardButton("🏠 Inicio", callback_data="patient_main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_doctor_contact_keyboard():
    """Teclado para doctores cuando consultan su propio contacto (solo volver)."""
    keyboard = [
        [InlineKeyboardButton("🏠 Inicio", callback_data="doctor_main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

