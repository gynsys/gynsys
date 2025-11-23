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


async def handle_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja todos los callbacks y los redirige según el rol del usuario
    """
    import logging
    logger = logging.getLogger(__name__)
    
    user_id = update.effective_user.id
    user_role = await role_manager.get_user_role(user_id)
    
    query = update.callback_query
    callback_data = query.data
    
    logger.info(f"[handle_all_callbacks] Callback recibido: {callback_data} - Usuario: {user_id} - Rol: {user_role}")
    print(f"🔔 Callback: {callback_data} - Usuario: {user_id} - Rol: {user_role}")  # DEBUG
    
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
    if callback_data in {"faq_next", "faq_prev", "faq_ignore"}:
        from features.faqs.user_handlers import navigate_faq_next, navigate_faq_previous, faq_ignore
        if callback_data == "faq_next":
            await navigate_faq_next(update, context)
        elif callback_data == "faq_prev":
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
    
    # Callbacks de Pacientes
    elif user_role == 'patient':
        await handle_patient_callback(update, context)
        return
    
    # Reintentar acceso
    elif callback_data == "retry_access":
        await start(update, context)

