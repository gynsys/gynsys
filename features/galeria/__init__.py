# features/galeria/__init__.py

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Importamos los tres módulos de handlers que hemos creado
from . import admin_handlers   # Para el SuperAdmin
from . import tenant_handlers  # Para los Inquilinos (Médicos)
from . import user_handlers    # Para la vista pública (Pacientes y visitantes)

def register(app: Application):
    """
    Registra todos los handlers para el módulo de galería, separando la lógica
    del SuperAdmin, los Inquilinos y los Usuarios finales.
    """
    
    # =================================================================
    # --- GRUPO 1: HANDLERS PARA EL SUPERADMIN (Panel del Bot Padre) ---
    # =================================================================
    # Usan el prefijo 'gallery_' y están protegidos por @superadmin_required
    
    SA_CONFIG = admin_handlers.CONFIG
    
    sa_cancel_handlers = [
        CommandHandler('cancelar', admin_handlers.cancel_gallery_conv),
        CallbackQueryHandler(admin_handlers.cancel_gallery_conv, pattern='^cancel_conv$')
    ]

    sa_add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.add_item_start, pattern=f"^{SA_CONFIG['prefix']}_add_start$")],
        states={
            admin_handlers.AWAITING_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.receive_title)],
            admin_handlers.AWAITING_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.receive_content)],
            admin_handlers.AWAITING_MEDIA: [MessageHandler(filters.PHOTO | filters.VIDEO, admin_handlers.save_new_item_with_media)],
        },
        fallbacks=sa_cancel_handlers,
        name="gallery_sa_add_conv"
    )

    sa_modify_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.modify_item_start, pattern=f"^{SA_CONFIG['prefix']}_modify_\\d+$")],
        states={
            admin_handlers.AWAITING_MOD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.receive_modified_title)],
            admin_handlers.AWAITING_MOD_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.receive_modified_content)],
            admin_handlers.AWAITING_MOD_MEDIA: [MessageHandler(filters.PHOTO | filters.VIDEO | (filters.TEXT & ~filters.COMMAND), admin_handlers.receive_modified_media_or_skip)],
        },
        fallbacks=sa_cancel_handlers,
        name="gallery_sa_modify_conv"
    )

    sa_edit_header_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_handlers.start_header_edit, pattern=f"^{SA_CONFIG['prefix']}_edit_header$")],
        states={admin_handlers.AWAITING_HEADER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handlers.save_modified_header)]},
        fallbacks=sa_cancel_handlers,
        name="gallery_sa_header_conv"
    )

    # Añadimos las conversaciones del SuperAdmin
    app.add_handler(sa_add_conv)
    app.add_handler(sa_modify_conv)
    app.add_handler(sa_edit_header_conv)

    # Añadimos los callbacks del SuperAdmin
    app.add_handler(CallbackQueryHandler(admin_handlers.galeria_hub, pattern=f"^{SA_CONFIG['prefix']}_admin_hub$"))
    app.add_handler(CallbackQueryHandler(admin_handlers.list_items_for_action, pattern=f"^{SA_CONFIG['prefix']}_(modify|delete)_list$"))
    app.add_handler(CallbackQueryHandler(admin_handlers.confirm_delete_item, pattern=f"^{SA_CONFIG['prefix']}_delete_\\d+$"))
    app.add_handler(CallbackQueryHandler(admin_handlers.execute_delete_item, pattern=f"^{SA_CONFIG['prefix']}_delete_execute_confirm_\\d+$"))


    # =================================================================
    # --- GRUPO 2: HANDLERS PARA LOS INQUILINOS (Panel del Médico) ---
    # =================================================================
    # Usan el prefijo 'gallery_tenant_' y están protegidos por @doctor_required
    
    TN_CONFIG = tenant_handlers.CONFIG.copy()
    TN_CONFIG['prefix'] = 'gallery_tenant' # Asignamos un prefijo único para evitar colisiones

    tn_cancel_handlers = [
        CommandHandler('cancelar_tenant', tenant_handlers.cancel_gallery_conv), # Usamos un comando diferente si es necesario
        CallbackQueryHandler(tenant_handlers.cancel_gallery_conv, pattern='^cancel_tenant_conv$')
    ]

    tn_add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(tenant_handlers.add_item_start, pattern=f"^{TN_CONFIG['prefix']}_add_start$")],
        states={
            tenant_handlers.AWAITING_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tenant_handlers.receive_title)],
            tenant_handlers.AWAITING_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tenant_handlers.receive_content)],
            tenant_handlers.AWAITING_MEDIA: [MessageHandler(filters.PHOTO | filters.VIDEO, tenant_handlers.save_new_item_with_media)],
        },
        fallbacks=tn_cancel_handlers,
        name="gallery_tn_add_conv"
    )
    
    tn_modify_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(tenant_handlers.modify_item_start, pattern=f"^{TN_CONFIG['prefix']}_modify_\\d+$")],
        states={
            tenant_handlers.AWAITING_MOD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tenant_handlers.receive_modified_title)],
            tenant_handlers.AWAITING_MOD_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tenant_handlers.receive_modified_content)],
            tenant_handlers.AWAITING_MOD_MEDIA: [MessageHandler(filters.PHOTO | filters.VIDEO | (filters.TEXT & ~filters.COMMAND), tenant_handlers.receive_modified_media_or_skip)],
        },
        fallbacks=tn_cancel_handlers,
        name="gallery_tn_modify_conv"
    )

    tn_edit_header_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(tenant_handlers.start_header_edit, pattern=f"^{TN_CONFIG['prefix']}_edit_header$")],
        states={tenant_handlers.AWAITING_HEADER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, tenant_handlers.save_modified_header)]},
        fallbacks=tn_cancel_handlers,
        name="gallery_tn_header_conv"
    )

    # Añadimos las conversaciones del Inquilino
    app.add_handler(tn_add_conv)
    app.add_handler(tn_modify_conv)
    app.add_handler(tn_edit_header_conv)

    # Añadimos los callbacks del Inquilino (nota el nuevo prefijo en los patterns)
    app.add_handler(CallbackQueryHandler(tenant_handlers.galeria_hub, pattern=f"^{TN_CONFIG['prefix']}_hub$")) # El botón del panel de médico ahora apunta aquí
    app.add_handler(CallbackQueryHandler(tenant_handlers.list_items_for_action, pattern=f"^{TN_CONFIG['prefix']}_(modify|delete)_list$"))
    app.add_handler(CallbackQueryHandler(tenant_handlers.confirm_delete_item, pattern=f"^{TN_CONFIG['prefix']}_delete_\\d+$"))
    app.add_handler(CallbackQueryHandler(tenant_handlers.execute_delete_item, pattern=f"^{TN_CONFIG['prefix']}_delete_execute_confirm_\\d+$"))


    # ===================================================================
    # --- GRUPO 3: HANDLERS PARA USUARIOS FINALES (Vista Pública) ---
    # ===================================================================
    # Estos son los que ven los pacientes y visitantes, no tienen edición.
    
    # El `callback_data` 'galeria_menu' es el punto de entrada para todos.
    app.add_handler(CallbackQueryHandler(user_handlers.show_galeria_menu, pattern='^galeria_menu$'))
    
    # Para ver un ítem específico, se usa 'gallery_item_'.
    # Usamos el prefijo del SuperAdmin porque es el original y no causa conflicto.
    app.add_handler(CallbackQueryHandler(user_handlers.show_galeria_content, pattern=f"^{SA_CONFIG['prefix']}_item_\\d+$"))