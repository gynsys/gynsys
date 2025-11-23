# features/pdf_configuration/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_configuration_keyboard(settings: dict) -> InlineKeyboardMarkup:
    """Genera el teclado principal de configuración"""

    keyboard = []

    # Fila 1: Incluir Test Endometriosis
    include_functional = settings.get('include_functional_exam', {}).get('value', '1') == '1'
    toggle_text = "✅ Incluir Test Endometriosis" if include_functional else "❌ Incluir Test Endometriosis"
    keyboard.append([
        InlineKeyboardButton(toggle_text, callback_data="pdf_toggle_functional_exam")
    ])

    # Fila 2: Datos del Médico
    keyboard.append([
        InlineKeyboardButton("👨‍⚕️ Datos del Médico", callback_data="pdf_config_medical_section")
    ])

    # Fila 3: Encabezado y Logos
    keyboard.append([
        InlineKeyboardButton("📝 Encabezado", callback_data="pdf_config_header_section"),
        InlineKeyboardButton("🖼️ Logos", callback_data="pdf_config_logos_section")
    ])

    '''
    keyboard.append([
        InlineKeyboardButton("📊 Vista Previa", callback_data="pdf_config_preview"),
        InlineKeyboardButton("🔄 Restablecer", callback_data="pdf_config_reset_confirm")
    ])'''

    # Fila 4: Volver
    keyboard.append([
        InlineKeyboardButton("🔙 Volver", callback_data="doctor_panel"),
        InlineKeyboardButton("🏠 ", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(keyboard)

def get_medical_section_keyboard(settings: dict) -> InlineKeyboardMarkup:
    """Teclado para la sección de datos del médico"""
    keyboard = []

    medical_fields = [
        ('doctor_name', '✏️ Nombre'),
        ('specialty', '✏️ Especialidad'),
        ('location', '✏️ Ubicación'),
        ('phones', '✏️ Teléfonos'),
        ('mpps_number', '✏️ MPPS'),
        ('cmdm_number', '✏️ CMDM'),
        ('doctor_id', '✏️ C.I. Médico')
    ]

    for key, label in medical_fields:
        visible = settings.get(key, {}).get('visible', True)
        toggle_icon = "👁️" if visible else "👁️‍🗨️"
        row = [
            InlineKeyboardButton(label, callback_data=f"pdf_edit_text:{key}"),
            InlineKeyboardButton(toggle_icon, callback_data=f"pdf_toggle_visibility:{key}")
        ]
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("🔙 Atrás", callback_data="pdf_config_main")
    ])

    return InlineKeyboardMarkup(keyboard)

def get_header_section_keyboard(settings: dict) -> InlineKeyboardMarkup:
    """Teclado para la sección de encabezado y pie"""
    keyboard = []

    header_fields = [
        ('report_title', '✏️ Título Informe'),
        ('footer_city', '✏️ Ciudad Pie')
    ]

    for key, label in header_fields:
        visible = settings.get(key, {}).get('visible', True)
        toggle_icon = "👁️" if visible else "👁️‍🗨️"
        row = [
            InlineKeyboardButton(label, callback_data=f"pdf_edit_text:{key}"),
            InlineKeyboardButton(toggle_icon, callback_data=f"pdf_toggle_visibility:{key}")
        ]
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("🔙 Atrás", callback_data="pdf_config_main")
    ])

    return InlineKeyboardMarkup(keyboard)

def get_logos_section_keyboard(settings: dict) -> InlineKeyboardMarkup:
    """Teclado para la sección de logos"""
    keyboard = []

    logo_fields = [
        ('logo_header_1', '🖼️ Logo Izquierdo'),
        ('logo_header_2', '🖼️ Logo Derecho'),
        ('logo_signature', '🖋️ Firma/Sello')
    ]

    for key, label in logo_fields:
        visible = settings.get(key, {}).get('visible', True)
        toggle_icon = "👁️" if visible else "👁️‍🗨️"
        value = settings.get(key, {}).get('value')

        row = [
            InlineKeyboardButton(label, callback_data=f"pdf_upload_logo:{key}"),
            InlineKeyboardButton(toggle_icon, callback_data=f"pdf_toggle_visibility:{key}")
        ]
        keyboard.append(row)

        # Botón de eliminar solo si hay logo cargado
        '''
        if value:
            keyboard.append([
                InlineKeyboardButton("🗑️ Eliminar", callback_data=f"pdf_delete_logo:{key}")
            ])
            '''
    keyboard.append([
        InlineKeyboardButton("🔙 Atrás", callback_data="pdf_config_main"),
        InlineKeyboardButton("🏠 ", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Teclado para cancelar operación"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ Cancelar", callback_data="pdf_config_cancel")
    ]])

def get_confirm_reset_keyboard() -> InlineKeyboardMarkup:
    """Teclado para confirmar restablecimiento"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Sí, restablecer", callback_data="pdf_config_reset_confirm"),
            InlineKeyboardButton("❌ No, mantener", callback_data="pdf_config_main")
        ]
    ])

def get_confirm_delete_keyboard(logo_key: str) -> InlineKeyboardMarkup:
    """Teclado para confirmar eliminación de logo"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Sí, eliminar", callback_data=f"pdf_delete_confirm:{logo_key}"),
            InlineKeyboardButton("❌ Cancelar", callback_data="pdf_config_logos_section")
        ]
    ])