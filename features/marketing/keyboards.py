from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_marketing_keyboard(is_superadmin: bool = False, is_doctor: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        # Fila 1: Sobre GynSys y Galería
        [
            InlineKeyboardButton("ℹ️ Sobre GynSys", callback_data="marketing_about"),
            InlineKeyboardButton("🖼️ Galería", callback_data="galeria_menu")
        ],
        # Fila 2: Quiero mi Bot
        [
            InlineKeyboardButton("🤖 Quiero mi Bot", callback_data="request_bot")
        ],
        # Fila 3: FAQs y Precios
        [
            InlineKeyboardButton("❓ FAQ", callback_data="faq_menu"),
            InlineKeyboardButton("💰 Precios", callback_data="marketing_pricing")
        ],
    ]

    # Botones adicionales para superadmin (menú privado)
    if is_superadmin:
        keyboard.append([
            InlineKeyboardButton("👨‍⚕️ Médicos", callback_data="doctors_menu"),
            InlineKeyboardButton("🏛 Panel Admin", callback_data="open_superadmin_panel")
        ])
        keyboard.append([
            InlineKeyboardButton("🆕 Solicitudes", callback_data="requests_menu")
        ])
    elif is_doctor:
        keyboard.append([
            InlineKeyboardButton("🛠 Panel Admin", callback_data="doctor_panel")
        ])

    return InlineKeyboardMarkup(keyboard)

