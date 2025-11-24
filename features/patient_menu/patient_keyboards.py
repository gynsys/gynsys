from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import extra_modules_db
from utils.role_manager import RoleManager
from config import DB_PATH

role_manager = RoleManager(DB_PATH)

async def get_patient_main_keyboard(doctor_id: int = None):
    """
    Menú principal para usuarios de los inquilinos (pacientes)
    
    Este menú debe reflejar EXACTAMENTE los mismos módulos activos que el doctor,
    pero SIN los botones administrativos (Gestión Historia, Panel Admin).
    
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
    
    # Verificar módulos activos para el doctor (igual que get_doctor_public_keyboard)
    active_modules = {}
    if doctor_id:
        # Verificar todos los módulos
        module_names = ['galeria', 'contacto', 'precios', 'faqs', 'citas', 'ubicaciones', 'test', 'quiz']
        for module_name in module_names:
            active_modules[module_name] = await extra_modules_db.is_module_active_for_doctor(doctor_id, module_name)
    
    # Fila 1: Módulos extra (test y quiz) - solo si están activos
    extra_buttons = []
    if active_modules.get('test', False):
        extra_buttons.append(InlineKeyboardButton("🧪 Test Endometriosis", callback_data="start_endo_test"))
    if active_modules.get('quiz', False):
        extra_buttons.append(InlineKeyboardButton("🎮 Aprende Jugando", callback_data="quiz_start_intro"))
    
    # Agregar botones de módulos extra en filas separadas
    for button in extra_buttons:
        keyboard.append([button])
    
    # Construir teclado principal según módulos activos (igual que get_doctor_public_keyboard)
    main_buttons = []
    
    # Fila: Galería y Precios (solo si están activos)
    row = []
    if active_modules.get('galeria', True):  # Por defecto True para compatibilidad
        row.append(InlineKeyboardButton("🖼️ Galería", callback_data="patient_gallery"))
    if active_modules.get('precios', True):
        row.append(InlineKeyboardButton("💰 Precios", callback_data="patient_pricing"))
    if row:
        main_buttons.append(row)
    
    # Fila: Citas y Contacto (solo si están activos)
    row = []
    if active_modules.get('citas', True):
        row.append(InlineKeyboardButton("📅 Citas", callback_data="patient_book_appointment"))
    if active_modules.get('contacto', True):
        row.append(InlineKeyboardButton("📞 Contacto", callback_data="patient_contact_doctor"))
    if row:
        main_buttons.append(row)
    
    # Fila: Ubicaciones y FAQ (solo si están activos)
    row = []
    if active_modules.get('ubicaciones', True):
        row.append(InlineKeyboardButton("📍 Ubicaciones", callback_data="patient_locations"))
    if active_modules.get('faqs', True):
        row.append(InlineKeyboardButton("❓ FAQ", callback_data="patient_faq"))
    if row:
        main_buttons.append(row)
    
    # Botón de compartir link (siempre visible, no es un módulo controlable)
    main_buttons.append([
        InlineKeyboardButton("🔗 Compartir link de mi médico", callback_data="patient_share_link")
    ])
    # ⚠️ NO AGREGAR "🏠 Inicio" AQUÍ - Ver documentación arriba
    # ⚠️ NO AGREGAR botones administrativos (Gestión Historia, Panel Admin) - Solo para doctores
    
    keyboard.extend(main_buttons)
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