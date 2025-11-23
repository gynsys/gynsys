from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import extra_modules_db
from utils.role_manager import RoleManager
from config import DB_PATH

role_manager = RoleManager(DB_PATH)

async def get_patient_main_keyboard(doctor_id: int = None):
    """
    Menú principal para usuarios de los inquilinos (pacientes)
    
    ============================================================
    ⚠️ REGLA IMPORTANTE: NO AGREGAR BOTÓN "🏠 Inicio" AQUÍ ⚠️
    ============================================================
    Los menús principales (doctor y paciente) NO deben tener botón "🏠 Inicio"
    porque ya están en el menú principal. El botón "🏠 Inicio" solo debe estar en:
    - Panel Admin (get_main_menu_keyboard cuando is_superadmin=False)
    - Submenús administrativos que necesiten volver al menú principal
    
    Este es el menú principal del paciente, no un submenú.
    ============================================================
    """
    keyboard = []
    
    # Fila 1: Verificar si los módulos extra están activos
    extra_buttons = []
    if doctor_id:
        # Verificar módulo test
        is_test_active = await extra_modules_db.is_module_active_for_doctor(doctor_id, 'test')
        if is_test_active:
            extra_buttons.append(InlineKeyboardButton("🧪 Test Endometriosis", callback_data="start_endo_test"))
        
        # Verificar módulo quiz
        is_quiz_active = await extra_modules_db.is_module_active_for_doctor(doctor_id, 'quiz')
        if is_quiz_active:
            extra_buttons.append(InlineKeyboardButton("🎮 Aprende Jugando", callback_data="quiz_start_intro"))
    
    # Agregar botones de módulos extra en filas separadas
    for button in extra_buttons:
        keyboard.append([button])
    
    keyboard.extend([
        [
            InlineKeyboardButton("🖼️ Galería", callback_data="patient_gallery"),
            InlineKeyboardButton("💰 Precios", callback_data="patient_pricing")
        ],
        [
            InlineKeyboardButton("📅 Citas", callback_data="patient_book_appointment"),
            InlineKeyboardButton("📞 Contacto", callback_data="patient_contact_doctor")
        ],
        [
            InlineKeyboardButton("📍 Ubicaciones", callback_data="patient_locations"),
            InlineKeyboardButton("❓ FAQ", callback_data="patient_faq")
        ],
        [
            InlineKeyboardButton("🔗 Compartir link de mi médico", callback_data="patient_share_link")
        ]
        # ⚠️ NO AGREGAR "🏠 Inicio" AQUÍ - Ver documentación arriba
    ])
    return InlineKeyboardMarkup(keyboard)

def get_doctor_selection_keyboard(doctors):
    """Teclado para seleccionar médico (nuevos usuarios)"""
    keyboard = []
    for doctor in doctors:
        # doctor[1] = nombre, doctor[0] = id
        keyboard.append([
            InlineKeyboardButton(f"👨‍⚕️ {doctor[1]}", 
                               callback_data=f"select_doctor_{doctor[0]}")
        ])
    
    keyboard.append([InlineKeyboardButton("🤖 Quiero mi Bot", callback_data="request_bot")])
    keyboard.append([InlineKeyboardButton("🏠 Inicio", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)