from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database import extra_modules_db
from utils.role_manager import RoleManager
from config import DB_PATH

role_manager = RoleManager(DB_PATH)

async def get_main_menu_keyboard(is_superadmin: bool, user_id: int = None):
    """
    Retorna el menú principal según el rol - Botones en filas de 2
    """
    if is_superadmin:
        # Menú SuperAdmin - Igual al público + botón Inicio
        keyboard = [
            # Fila 1: Sobre GynSys y Galería
            [
                InlineKeyboardButton("ℹ️ Sobre GynSys", callback_data="marketing_about")],
            [    InlineKeyboardButton("🖼️ Galería", callback_data="gallery_admin_hub")],
            # Fila 2: Quiero mi Bot
            [
                InlineKeyboardButton("🤖 Quiero mi Bot", callback_data="request_bot")
            ],
            # Fila 3: FAQs y Precios
            [ InlineKeyboardButton("❓ FAQ", callback_data="faqs_admin_hub_v2")],

            [ InlineKeyboardButton("💰 Precios", callback_data="marketing_pricing")],
            # Fila 4: Editar Mensaje de Bienvenida
            [
                InlineKeyboardButton("✏️ Editar msg Bienvenida", callback_data="edit_welcome_message")
            ],
            # Fila 5: Inicio
            [
                InlineKeyboardButton("🏠 ", callback_data="main_menu")
            ]
        ]
    else:
        # ============================================================
        # PANEL ADMIN DEL INQUILINO (NO confundir con menú principal)
        # ============================================================
        # Este teclado se usa en: show_doctor_panel() -> Panel Admin
        #
        # DIFERENCIAS IMPORTANTES:
        # - Panel Admin: Para GESTIONAR el bot (configurar, administrar)
        #   - Incluye: "🧪 Gestionar Test" (para administrar preguntas)
        #   - NO incluye: "🧪 Test Endometriosis" (ese va en menú principal)
        #   - SIEMPRE incluye: "🏠 Inicio" (para volver al menú principal)
        #
        # - Menú Principal: Para que el doctor vea/comparta con pacientes
        #   - Incluye: "🧪 Test Endometriosis" (para verlo/compartirlo)
        #   - Generado por: get_doctor_public_keyboard()
        # ============================================================
        keyboard = []

        # Verificar si el módulo test está activo para mostrar "Gestionar Test"
        test_manage_button = None
        team_manage_button = None
        if user_id:
            doctor = await role_manager.get_doctor_by_telegram_id(user_id)
            if doctor:
                doctor_id = doctor[0]
                is_test_active = await extra_modules_db.is_module_active_for_doctor(doctor_id, 'test')
                if is_test_active:
                    test_manage_button = InlineKeyboardButton("🧪 Gestionar Test", callback_data="test_admin_hub")
                
                is_team_active = await extra_modules_db.is_module_active_for_doctor(doctor_id, 'equipo')
                if is_team_active:
                    team_manage_button = InlineKeyboardButton("👥 Gestión Equipo", callback_data="team_admin_hub")

        # Fila 1
        keyboard.append([
            InlineKeyboardButton("📅 Citas", callback_data="citas_menu"),
        ])
        # Fila 2
        keyboard.append([
            InlineKeyboardButton("🖼️ Galería", callback_data="gallery_tenant_hub"),

        ])

        # Fila 3
        keyboard.append([

            InlineKeyboardButton("❓ FAQ", callback_data="faqs_admin_hub")
        ])
        # Fila 4
        keyboard.append([

            InlineKeyboardButton("📍 Ubicaciones", callback_data="locations_admin_hub")
        ])
        # Fila 5
        keyboard.append([
            InlineKeyboardButton("📞 Contacto", callback_data="contacto_menu")

        ])
        keyboard.append([

            InlineKeyboardButton("💰 Precios", callback_data="prices_admin_hub")
        ])
        # Fila 5 - Configuración PDF
        keyboard.append([
            InlineKeyboardButton("⚙️ Config. Informe PDF", callback_data="pdf_configuration_menu")
        ])

        # Fila 6 - Editar Mensaje de Bienvenida
        keyboard.append([
            InlineKeyboardButton("✏️ Editar msg Bienvenida", callback_data="edit_welcome_message")
        ])

        # Fila 7 - Gestionar Test (solo si el módulo está activo)
        if test_manage_button:
            keyboard.append([test_manage_button])
            
        # Fila 7.5 - Gestionar Equipo (solo si el módulo está activo)
        if team_manage_button:
            keyboard.append([team_manage_button])

        # Fila 8 - IMPORTANTE: Siempre incluir botón Inicio en el Panel Admin
        # Este botón permite volver al menú principal del doctor
        keyboard.append([
            InlineKeyboardButton("🏠", callback_data="doctor_main_menu")
        ])

    return InlineKeyboardMarkup(keyboard)

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