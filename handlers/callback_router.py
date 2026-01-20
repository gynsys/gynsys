"""
Router central para manejar todos los callbacks del bot
"""
from telegram import Update
from telegram.ext import ContextTypes

from utils.role_manager import RoleManager
from config import DB_PATH
from features.admin import superadmin_main_menu, handle_superadmin_callback
from features.main_menu.user_handler import admin_main_menu, handle_admin_callback
from features.patient_menu.patient_handler import patient_main_menu, handle_patient_callback
from features.marketing.handler import send_marketing_menu, handle_marketing_callback
from handlers.start_handler import start
from handlers.inactive_doctor_handler import show_inactive_doctor_message

role_manager = RoleManager(DB_PATH)


def _is_callback_handled_by_router(callback_data: str, user_role: str) -> bool:
    """
    Verifica si un callback debe ser manejado por el router genérico.
    Retorna True si el callback está en la whitelist, False si debe ser ignorado
    para permitir que los handlers específicos lo capturen.
    """
    # Callbacks que el router maneja directamente (sin importar el rol)
    direct_callbacks = {
        "main_menu", "retry_access", "open_superadmin_panel",
        "faq_menu", "doctor_faq", "patient_faq", "faq", "faq_ignore",
        "test_answer_yes", "test_answer_no", "cancel_test", "begin_test"
    }
    
    # Patrones de callbacks que el router maneja directamente
    direct_patterns = [
        "marketing_",
        "faq_next",
        "faq_prev"
    ]
    
    # Verificar callbacks directos
    if callback_data in direct_callbacks:
        return True
    
    # Verificar patrones directos
    for pattern in direct_patterns:
        if callback_data.startswith(pattern):
            return True
    
    # Callbacks que maneja handle_admin_callback (para doctores)
    if user_role == 'doctor':
        admin_callbacks = {
            "doctor_main_menu", "doctor_panel", "doctor_contact",
            "contacto_menu", "contact_preview", "doctor_pricing",
            "doctor_citas", "locations_admin_hub", "faqs_admin_hub", "faqs_admin_hub_v2",
            "prices_admin_hub", "test_admin_hub", "precios_menu",
            "doctor_locations", "doctor_faq", "doctor_share_link",
            "admin_panel", "settings_menu"
        }
        
        admin_patterns = [
            "citas_view_", "citas_detail_", "citas_action_", "citas_confirm_",
            "resched_cal_", "reschedule_"
        ]
        
        if callback_data in admin_callbacks:
            return True
        
        for pattern in admin_patterns:
            if callback_data.startswith(pattern):
                return True
    
    # Callbacks que maneja handle_superadmin_callback (para superadmin)
    if user_role == 'superadmin':
        superadmin_callbacks = {
            "doctors_menu", "requests_menu", "add_doctor", "list_doctors",
            "restrict_doctor", "delete_doctor_menu", "simple_restrict_menu",
            "simple_permit_menu", "refresh_doctors", "refresh_restricted",
            "list_restricted", "extra_modules_hub", "extra_modules_by_doctor",
            "locations_admin_hub", "faqs_admin_hub", "faqs_admin_hub_v2", "contacto_menu", "contact_preview"
        }
        
        superadmin_patterns = [
            "doctors_page_", "delete_doctor_page_", "simple_restrict_page_",
            "simple_permit_page_", "delete_doctor_", "restrict_doctor_",
            "simple_delete_", "simple_restrict_", "simple_permit_",
            "request_detail_", "request_approve_", "request_reject_",
            "extra_modules_page_", "doctors_modules_page_",
            "extra_modules_doctor_", "extra_modules_toggle_"
        ]
        
        if callback_data in superadmin_callbacks:
            return True
        
        for pattern in superadmin_patterns:
            if callback_data.startswith(pattern):
                return True
    
    # Si no está en ninguna whitelist, NO lo maneja el router
    return False


async def handle_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja todos los callbacks y los redirige según el rol del usuario.
    Solo procesa callbacks que explícitamente reconoce (whitelist).
    Los demás callbacks son ignorados para permitir que los handlers específicos los capturen.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    user_id = update.effective_user.id
    user_role = await role_manager.get_user_role(user_id)
    
    query = update.callback_query
    callback_data = query.data
    
    print(f"🔍 [DEBUG] Callback recibido: '{callback_data}' | Usuario: {user_id} | Rol: {user_role}")
    logger.info(f"[handle_all_callbacks] Callback recibido: {callback_data} - Usuario: {user_id} - Rol: {user_role}")
    print(f"🔔 Callback: {callback_data} - Usuario: {user_id} - Rol: {user_role}")  # DEBUG
    
    # Verificar si el callback debe ser manejado por el router genérico
    # EXCEPCIÓN: Si es paciente, los callbacks de pacientes deben ir a handle_patient_callback
    if user_role == 'patient' and (
        callback_data.startswith("patient_") or 
        callback_data in {"start_endo_test", "quiz_start_intro"} or
        callback_data.startswith("book_") or
        callback_data.startswith("select_doctor_")
    ):
        # Callbacks de pacientes - redirigir a handle_patient_callback
        await handle_patient_callback(update, context)
        return
    
    if not _is_callback_handled_by_router(callback_data, user_role):
        # Callback no reconocido - ignorar y permitir que handlers específicos lo capturen
        logger.debug(f"[handle_all_callbacks] Callback '{callback_data}' no está en la whitelist - ignorando para permitir que handlers específicos lo capturen")
        # ⚠️ NO responder aquí - deja que el handler específico responda (incluso con show_alert)
        # await query.answer()  # COMENTADO: Esto previene que handlers muestren alerts
        return
    
    # ⚠️ IMPORTANTE: Los callbacks del test deben ser manejados por el ConversationHandler
    # Si llegamos aquí con un callback del test, significa que el ConversationHandler no lo capturó
    # Esto puede pasar si el usuario no está en una conversación activa del test
    # En ese caso, simplemente ignoramos el callback
    if callback_data in {"test_answer_yes", "test_answer_no", "cancel_test", "begin_test"}:
        logger.warning(f"[handle_all_callbacks] Callback del test '{callback_data}' llegó a handle_all_callbacks - el ConversationHandler debería haberlo capturado")
        # No hacer nada - el callback ya fue procesado o ignorado
        await query.answer()  # OK aquí porque es un callback órfano
        return
    
    # Si el usuario es médico inactivo, mostrar mensaje de renovación
    if user_role == 'inactive_doctor':
        await show_inactive_doctor_message(update, context)
        return
    
    # Handlers específicos de FAQs (deben ir antes de la redirección por rol)
    if callback_data in {"faq_menu", "doctor_faq", "patient_faq", "faq"}:
        from features.faqs.user_handlers import show_faqs_menu
        await show_faqs_menu(update, context)
        return
    
    # Handlers de navegación de FAQs (deben ir antes de la redirección por rol)
    # Soporta tanto el formato antiguo (faq_next, faq_prev) como el nuevo (faq_next_bot_id_item_id)
    if callback_data.startswith("faq_next") or callback_data.startswith("faq_prev") or callback_data == "faq_ignore":
        from features.faqs.user_handlers import navigate_faq_next, navigate_faq_previous, faq_ignore
        if callback_data.startswith("faq_next"):
            await navigate_faq_next(update, context)
        elif callback_data.startswith("faq_prev"):
            await navigate_faq_previous(update, context)
        elif callback_data == "faq_ignore":
            await faq_ignore(update, context)
        return

    if callback_data == "main_menu":
        if user_role == 'superadmin':
            await send_marketing_menu(update, context, is_superadmin=True)
        elif user_role == 'doctor':
            # Para doctores, enviar su menú principal de inquilino
            await admin_main_menu(update, context)
        elif user_role == 'patient':
            # Para pacientes, mostrar su menú principal (NO marketing)
            doctor = await role_manager.get_assigned_doctor(user_id)
            if doctor:
                await patient_main_menu(update, context, doctor[0])
            else:
                # Si no tiene doctor, mostrar marketing
                await send_marketing_menu(update, context)
        elif user_role == 'new_user':
            await send_marketing_menu(update, context)
        return

    if callback_data.startswith("marketing_"):
        await handle_marketing_callback(update, context)
        return
    if callback_data == "open_superadmin_panel":
        await superadmin_main_menu(update, context)
        return
    
    # Callbacks específicos de SuperAdmin
    elif user_role == 'superadmin':
        logger.info(f"[handle_all_callbacks] Redirigiendo callback '{callback_data}' a handle_superadmin_callback")
        await handle_superadmin_callback(update, context)
        logger.info(f"[handle_all_callbacks] handle_superadmin_callback completado para '{callback_data}'")
    
    # Callbacks de Médicos activos
    elif user_role == 'doctor':
        await handle_admin_callback(update, context)
    
    # Callbacks de Pacientes (ya manejados arriba, pero mantener como fallback)
    elif user_role == 'patient':
        # Si llegamos aquí, el callback no fue capturado arriba, intentar handle_patient_callback
        await handle_patient_callback(update, context)
        return
    
    # Reintentar acceso
    elif callback_data == "retry_access":
        await start(update, context)

