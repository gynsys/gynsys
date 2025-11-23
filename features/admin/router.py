"""
Router: El "Semáforo" (despachador de callbacks)
Mapea callbacks a handlers específicos de forma limpia y organizada.
"""
from telegram import Update
from telegram.ext import ContextTypes
from utils.logger import get_logger
from features.doctors.management_handler import doctors_management
from features.contacto.user_handler import show_contact_menu, show_contact_preview
from .handlers.menu_handlers import superadmin_main_menu, show_doctors_menu
from .handlers.doctor_handlers import (
    show_doctors_list,
    show_delete_menu,
    show_simple_restrict_menu,
    show_simple_permit_menu,
    simple_delete_doctor,
    simple_restrict_doctor,
    simple_permit_doctor,
    show_restrict_doctor,
)
from .handlers.request_handlers import (
    show_requests_menu,
    show_request_detail,
    approve_request,
    reject_request,
)

logger = get_logger("AdminRouter")


async def handle_superadmin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja callbacks específicos del SuperAdmin.
    Despacha callbacks a handlers específicos según el patrón.
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    logger.info(f"[handle_superadmin_callback] INICIO - Callback: {callback_data}, User ID: {update.effective_user.id}")
    print(f"🔄 Callback SuperAdmin: {callback_data}")
    
    # === MENÚS PRINCIPALES ===
    if callback_data == "main_menu":
        await superadmin_main_menu(update, context)
        return
    elif callback_data == "doctors_menu":
        await show_doctors_menu(update, context)
        return
    elif callback_data == "requests_menu":
        await show_requests_menu(update, context)
        return
    
    # === GESTIÓN DE MÉDICOS ===
    elif callback_data == "add_doctor":
        # Este se maneja en el ConversationHandler, no aquí
        return
    elif callback_data == "list_doctors":
        await show_doctors_list(update, context)
        return
    elif callback_data == "restrict_doctor":
        await show_restrict_doctor(update, context)
        return
    elif callback_data == "delete_doctor_menu":
        await show_delete_menu(update, context)
        return
    elif callback_data == "simple_restrict_menu":
        await show_simple_restrict_menu(update, context)
        return
    elif callback_data == "simple_permit_menu":
        await show_simple_permit_menu(update, context)
        return
    
    # === PAGINACIÓN DE MÉDICOS ===
    elif callback_data.startswith("doctors_page_"):
        page = int(callback_data.split("_")[2])
        await doctors_management.show_doctors_management(update, context, page)
        return
    elif callback_data.startswith("delete_doctor_page_"):
        page = int(callback_data.split("_")[3])
        await show_delete_menu(update, context, page)
        return
    elif callback_data.startswith("simple_restrict_page_"):
        page = int(callback_data.split("_")[3])
        await show_simple_restrict_menu(update, context, page)
        return
    elif callback_data.startswith("simple_permit_page_"):
        page = int(callback_data.split("_")[3])
        await show_simple_permit_menu(update, context, page)
        return
    
    # === ACCIONES DE MÉDICOS ===
    elif callback_data.startswith("delete_doctor_"):
        doctor_id = int(callback_data.split("_")[2])
        await doctors_management.handle_delete_doctor(update, context, doctor_id)
        return
    elif callback_data.startswith("restrict_doctor_"):
        doctor_id = int(callback_data.split("_")[2])
        await doctors_management.handle_restrict_doctor(update, context, doctor_id)
        return
    elif callback_data.startswith("simple_delete_"):
        doctor_id = int(callback_data.split("_")[2])
        await simple_delete_doctor(update, context, doctor_id)
        return
    elif callback_data.startswith("simple_restrict_"):
        doctor_id = int(callback_data.split("_")[2])
        await simple_restrict_doctor(update, context, doctor_id)
        return
    elif callback_data.startswith("simple_permit_"):
        doctor_id = int(callback_data.split("_")[2])
        await simple_permit_doctor(update, context, doctor_id)
        return
    elif callback_data == "refresh_doctors":
        await doctors_management.show_doctors_management(update, context, page=0)
        return
    elif callback_data == "refresh_restricted":
        await doctors_management.show_restricted_doctors(update, context)
        return
    elif callback_data == "list_restricted":
        # TODO: Implementar si es necesario
        logger.warning("Callback 'list_restricted' no implementado")
        return
    
    # === SOLICITUDES ===
    elif callback_data.startswith("request_detail_"):
        request_id = int(callback_data.split("_")[2])
        await show_request_detail(update, context, request_id)
        return
    elif callback_data.startswith("request_approve_"):
        request_id = int(callback_data.split("_")[2])
        await approve_request(update, context, request_id)
        return
    elif callback_data.startswith("request_reject_"):
        request_id = int(callback_data.split("_")[2])
        await reject_request(update, context, request_id)
        return
    
    # === MÓDULOS EXTRAS ===
    elif callback_data.startswith("extra_modules"):
        from features.extra_modules.admin_handlers import (
            extra_modules_hub,
            list_doctors_for_modules,
            show_doctor_modules,
            toggle_doctor_module
        )
        if callback_data == "extra_modules_hub":
            await extra_modules_hub(update, context)
        elif callback_data == "extra_modules_by_doctor":
            await list_doctors_for_modules(update, context)
        elif callback_data.startswith("extra_modules_page_"):
            await list_doctors_for_modules(update, context)
        elif callback_data.startswith("extra_modules_doctor_"):
            await show_doctor_modules(update, context)
        elif callback_data.startswith("extra_modules_toggle_"):
            await toggle_doctor_module(update, context)
        return
    
    # === UBICACIONES ===
    elif callback_data == "locations_admin_hub":
        from features.ubicaciones.admin_handlers import locations_hub
        await locations_hub(update, context)
        return
    
    # === FAQs ===
    elif callback_data == "faqs_admin_hub":
        logger.info(f"[handle_superadmin_callback] ✅ Callback faqs_admin_hub detectado. User ID: {update.effective_user.id}")
        try:
            from features.faqs.admin_handlers import faqs_hub
            logger.info(f"[handle_superadmin_callback] Import exitoso, llamando a faqs_hub...")
            await faqs_hub(update, context)
            logger.info(f"[handle_superadmin_callback] ✅ faqs_hub completado exitosamente")
        except Exception as e:
            logger.error(f"[handle_superadmin_callback] ❌ Error al llamar faqs_hub: {e}", exc_info=True)
            await query.edit_message_text(f"❌ Error al acceder a FAQs: {str(e)}")
        return
    
    # === CONTACTO ===
    elif callback_data == "contacto_menu":
        await show_contact_menu(update, context)
        return
    elif callback_data == "contact_preview":
        await show_contact_preview(update, context)
        return
    
    # === CALLBACK NO MANEJADO ===
    else:
        logger.warning(f"[handle_superadmin_callback] ⚠️ Callback '{callback_data}' no manejado en handle_superadmin_callback")

