import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from features.main_menu.keyboards import get_main_menu_keyboard
from config import DB_PATH
from utils.role_manager import RoleManager

logger = logging.getLogger(__name__)
from features.contacto.user_handler import (
    show_contact_menu,
    show_contact_preview,
)
from features.ubicaciones.user_handlers import show_doctor_locations_menu
# FAQ edición por inquilino removida

role_manager = RoleManager(DB_PATH)


async def get_doctor_public_keyboard(user_id: int = None):
    """
    Genera el teclado del MENÚ PRINCIPAL del doctor (NO el Panel Admin)
    
    Este es el menú que el doctor ve y comparte con sus pacientes.
    
    ============================================================
    ⚠️ REGLA IMPORTANTE: NO AGREGAR BOTÓN "🏠 Inicio" AQUÍ ⚠️
    ============================================================
    Los menús principales (doctor y paciente) NO deben tener botón "🏠 Inicio"
    porque ya están en el menú principal. El botón "🏠 Inicio" solo debe estar en:
    - Panel Admin (get_main_menu_keyboard cuando is_superadmin=False)
    - Submenús administrativos que necesiten volver al menú principal
    
    DIFERENCIA con Panel Admin:
    - Menú Principal (este): Para ver/compartir con pacientes
      - Incluye: "🧪 Test Endometriosis" (si está activo)
      - NO incluye: "🏠 Inicio" (ya estamos en el menú principal)
      - Generado por: admin_main_menu()
    - Panel Admin: Para gestionar/configurar el bot
      - Incluye: "🧪 Gestionar Test" (si está activo)
      - Incluye: "🏠 Inicio" (para volver al menú principal)
      - Generado por: show_doctor_panel()
    ============================================================
    """
    keyboard = []
    
    # Verificar módulos activos para el doctor y si es titular
    active_modules = {}
    is_titular = True
    
    if user_id:
        from database.session import get_session
        from database.repositories.user_repository import InstitutionUserRepository
        
        async with get_session() as session:
            inst_repo = InstitutionUserRepository(session)
            # Si el user_id está en institution_users, NO es titular
            if await inst_repo.get_institution_user(user_id):
                is_titular = False
        
        doctor = await role_manager.get_doctor_by_telegram_id(user_id)
        if doctor:
            doctor_id = doctor[0]
            from database import extra_modules_db
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
    
    # Construir teclado principal según módulos activos
    main_buttons = []
    
    # Fila: Galería y Precios (solo si están activos)
    row = []
    if active_modules.get('galeria', True):  # Por defecto True para compatibilidad
        row.append(InlineKeyboardButton("🖼️ Galería", callback_data="galeria_menu"))
    if active_modules.get('precios', True):
        row.append(InlineKeyboardButton("💰 Precios", callback_data="doctor_pricing"))
    if row:
        main_buttons.append(row)
    
    # Fila: Citas y Contacto (solo si están activos)
    row = []
    if active_modules.get('citas', True):
        row.append(InlineKeyboardButton("📅 Citas", callback_data="doctor_citas"))
    if active_modules.get('contacto', True):
        row.append(InlineKeyboardButton("📞 Contacto", callback_data="doctor_contact"))
    if row:
        main_buttons.append(row)
    
    # Fila: Ubicaciones y FAQ (solo si están activos)
    row = []
    if active_modules.get('ubicaciones', True):
        row.append(InlineKeyboardButton("📍 Ubicaciones", callback_data="doctor_locations"))
    if active_modules.get('faqs', True):
        row.append(InlineKeyboardButton("❓ FAQ", callback_data="doctor_faq"))
    if row:
        main_buttons.append(row)
    
    
    # Siempre mostrar estos botones (no son módulos controlables)
    main_buttons.extend([
        [
            InlineKeyboardButton("📋 Gestión Historia", callback_data="patient_management_hub"),
        ],
        [
            InlineKeyboardButton("🔗 Compartir link", callback_data="doctor_share_link"),
        ]
    ])
    
    # ⚠️ REGLA: El Panel Admin SOLO es para el dueño del tenant (Is Titular)
    if is_titular:
        main_buttons.append([
            InlineKeyboardButton("⚙️ Panel Admin", callback_data="doctor_panel"),
        ])
    
    keyboard.extend(main_buttons)
    return InlineKeyboardMarkup(keyboard)


async def admin_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await role_manager.is_doctor_active(user_id):
        from main import show_inactive_doctor_message
        await show_inactive_doctor_message(update, context)
        return

    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    doctor_name = doctor[1] if doctor else "Tu perfil"
    
    # Obtener bot_id para el mensaje de bienvenida
    from common.context_manager import get_tenant_id
    bot_id = await get_tenant_id(update, context)
    if not bot_id and doctor:
        # Fallback: obtener bot_id desde doctor
        import aiosqlite
        from config import DB_PATH
        async with aiosqlite.connect(DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                'SELECT id FROM bots WHERE admin_user_id = ? AND is_active = 1',
                (doctor[2],)  # telegram_id
            )
            result = await cursor.fetchone()
            if result:
                bot_id = result['id']
    
    # Obtener mensaje de bienvenida personalizado
    from common import texts
    
    user_name = update.effective_user.first_name or "Usuario"
    mensaje_bienvenida = await texts.get_mensaje_bienvenida(nombre_usuario=user_name, bot_id=bot_id if bot_id else 1)
    
    # Construir mensaje final
    message = (
        #f"👋 Hello! Soy {doctor_name}</b>\n"
        #f"👋<b> Hello! Soy 💘 {doctor_name}</b>\n {mensaje_bienvenida}\n\n"
        f"{mensaje_bienvenida}"
      
        
    )
    
    keyboard = await get_doctor_public_keyboard(user_id=user_id)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


async def show_doctor_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = await get_main_menu_keyboard(is_superadmin=False, user_id=user_id)
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "⚙️ <b>Panel Admin</b>\nSelecciona una opción para administrar tu bot.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "⚙️ <b>Panel Admin</b>\nSelecciona una opción para administrar tu bot.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )


async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Permitir acceso al superadmin
    from config import SUPER_ADMIN_ID
    if user_id != SUPER_ADMIN_ID and not await role_manager.is_doctor_active(user_id):
        from main import show_inactive_doctor_message
        await show_inactive_doctor_message(update, context)
        return

    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data in {"main_menu", "doctor_main_menu"}:
        await admin_main_menu(update, context)
    elif callback_data == "doctor_panel":
        await show_doctor_panel(update, context)
    elif callback_data == "doctor_contact":
        from features.contacto.user_handler import show_doctor_contact_link
        await show_doctor_contact_link(update, context)
    elif callback_data == "contacto_menu":
        # edición desde panel admin (si se necesitara)
        await show_contact_menu(update, context)
    elif callback_data == "contact_preview":
        await show_contact_preview(update, context)
    elif callback_data == "doctor_pricing":
        from features.precios.user_handlers import show_precios_menu
        await show_precios_menu(update, context)
        return
    elif callback_data == "doctor_citas":
        from features.citas.admin_handlers import doctor_citas_menu
        await doctor_citas_menu(update, context)
        return
    elif callback_data.startswith(("citas_view_", "citas_detail_")):
        from features.citas.admin_handlers import list_and_detail_handler
        await list_and_detail_handler(update, context)
        return
    elif callback_data.startswith(("citas_action_", "citas_confirm_")):
        from features.citas.admin_handlers import action_handler
        await action_handler(update, context)
        return
    elif callback_data.startswith("resched_cal_"):
        logger.info(f"[user_handler] resched_cal callback recibido: {callback_data}")
        from features.citas.admin_handlers import calendar_handler
        await calendar_handler(update, context)
        return
    elif callback_data.startswith("reschedule_"):
        from features.citas.admin_handlers import reschedule_time_handler
        await reschedule_time_handler(update, context)
        return
    elif callback_data == "locations_admin_hub":
        from features.ubicaciones.admin_handlers import locations_hub
        await locations_hub(update, context)
    elif callback_data == "patient_management_hub":
        from features.preconsultas_admin.admin_handlers import patient_management_hub
        await patient_management_hub(update, context)
        return
    elif callback_data == "faqs_admin_hub" or callback_data == "faqs_admin_hub_v2":
        logger.info(f"[handle_admin_callback] Callback faqs_admin_hub recibido. User ID: {user_id}")
        from features.faqs.admin_handlers import faqs_hub
        logger.info(f"[handle_admin_callback] Llamando a faqs_hub...")
        await faqs_hub(update, context)
        logger.info(f"[handle_admin_callback] faqs_hub completado")
    elif callback_data == "prices_admin_hub":
        from features.precios.admin_handlers import prices_hub
        await prices_hub(update, context)
    elif callback_data == "test_admin_hub":
        from features.test.admin_handlers import test_hub
        await test_hub(update, context)
        return
    elif callback_data == "team_admin_hub" or callback_data.startswith("team_"):
        from features.team.admin_handlers import team_action_handler
        await team_action_handler(update, context)
        return
    elif callback_data == "precios_menu":
        from features.precios.user_handlers import show_precios_menu
        await show_precios_menu(update, context)
        return
    elif callback_data == "faq_menu":
        from features.faqs.user_handlers import show_faqs_menu
        await show_faqs_menu(update, context)
        return
    elif callback_data == "doctor_locations":
        await show_doctor_locations_menu(update, context)
    elif callback_data == "doctor_faq":
        from features.faqs.user_handlers import show_faqs_menu
        await show_faqs_menu(update, context)
        return
    elif callback_data == "doctor_share_link":
        # Mostrar link y código para que el médico lo comparta con pacientes
        from features.share_link.handlers import show_doctor_share_link
        
        doctor = await role_manager.get_doctor_by_telegram_id(user_id)
        if not doctor:
            keyboard = await get_doctor_public_keyboard(user_id=user_id)
            await query.edit_message_text(
                "⚠️ Solo los médicos activos pueden ver su enlace para compartir.",
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            return

        doctor_id, doctor_name = doctor[0], doctor[1]
        await show_doctor_share_link(update, context, doctor_id, doctor_name)
    elif callback_data == "admin_panel" or callback_data == "settings_menu":
        # Redirigir al panel de administración
        await show_doctor_panel(update, context)

    # Edición de FAQ removida