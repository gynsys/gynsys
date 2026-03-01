"""
Registro de todos los handlers del bot
"""
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)

from features.admin import (
    start_add_doctor,
    receive_doctor_name,
    receive_doctor_id,
    cancel_add_doctor,
    WAITING_FOR_DOCTOR_NAME,
    WAITING_FOR_DOCTOR_ID
)
from features.contacto.user_handler import (
    show_contact_menu,
    start_contact_edit,
    receive_contact_value,
    cancel_contact_edit,
    CONTACT_WAITING_VALUE,
)
from features.doctor_requests.handler import (
    start_request_bot,
    receive_full_name,
    receive_telegram_id,
    cancel_request,
    handle_payment_creation,
    check_payment_status,
    handle_pago_movil_selection,
    confirm_pago_movil,
    receive_pago_movil_reference,
    REQUEST_WAITING_NAME,
    REQUEST_WAITING_TELEGRAM_ID,
    REQUEST_WAITING_PAYMENT,
    REQUEST_WAITING_REFERENCE,
)
from features.galeria import register as register_galeria_handlers
from features.ubicaciones.user_handlers import register as register_locations_handlers
from features.ubicaciones.admin_handlers import register as register_locations_admin_handlers
from features.faqs.user_handlers import register as register_faqs_handlers
from features.faqs.admin_handlers import register as register_faqs_admin_handlers
from features.precios.user_handlers import register as register_precios_handlers
from features.precios.admin_handlers import register as register_precios_admin_handlers
from features.extra_modules.admin_handlers import register as register_extra_modules_handlers
from features.test.admin_handlers import register as register_test_admin_handlers
from features.test.user_handlers import register as register_test_user_handlers
from features.quiz.user_handlers import register as register_quiz_handlers
from features.welcome_message.handlers import register as register_welcome_message_handlers
from features.team.admin_handlers import register as register_team_handlers
from features.citas.user_handlers import (
    start_booking,
    handle_name,
    handle_consultation_type,
    handle_pregnancy_info,
    handle_reason,
    handle_location,
    calendar_handler_booking,
    handle_time,
    confirm_appointment,
    back_to_main_menu,
    back_to_locations,
    cancel_booking,
    AWAITING_NAME,
    SELECTING_CONSULTATION_TYPE,
    AWAITING_PREGNANCY_INFO,
    AWAITING_REASON,
    SELECTING_LOCATION,
    SELECTING_DATE,
    SELECTING_TIME,
    CONFIRMING,
    FINAL_STATE,
)
from handlers.start_handler import start
from handlers.callback_router import handle_all_callbacks


def register_all_handlers(application: Application):
    """
    Registra todos los handlers del bot en la aplicación
    """
    # Handlers de comandos básicos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", start))
    
    # Registrar handlers de módulos
    register_galeria_handlers(application)
    register_locations_handlers(application)
    register_locations_admin_handlers(application)
    register_faqs_handlers(application)
    register_faqs_admin_handlers(application)
    register_precios_handlers(application)
    register_precios_admin_handlers(application)
    register_extra_modules_handlers(application)
    register_test_admin_handlers(application)
    # ⚠️ IMPORTANTE: El ConversationHandler del test debe registrarse ANTES de handle_all_callbacks
    # para que pueda capturar los callbacks test_answer_yes, test_answer_no, cancel_test
    register_test_user_handlers(application)
    register_quiz_handlers(application)
    register_welcome_message_handlers(application)
    register_team_handlers(application)
    
    # ConversationHandler para agregar médicos
    add_doctor_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_add_doctor, pattern='^add_doctor$')
        ],
        states={
            WAITING_FOR_DOCTOR_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_doctor_name),
                CommandHandler('cancel', cancel_add_doctor)
            ],
            WAITING_FOR_DOCTOR_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_doctor_id),
                CommandHandler('cancel', cancel_add_doctor)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel_add_doctor)],
        name="add_doctor_conversation",
        persistent=True
    )
    application.add_handler(add_doctor_conv_handler)
    
    # ⚠️ IMPORTANTE: ConversationHandler para solicitar bot
    # Este handler es CRÍTICO para el flujo de onboarding de nuevos inquilinos.
    # NO modificar sin revisar cuidadosamente:
    # - receive_full_name DEBE retornar REQUEST_WAITING_TELEGRAM_ID
    # - receive_telegram_id DEBE retornar ConversationHandler.END
    # - El orden de los handlers es importante (debe ir antes de handlers genéricos)
    request_bot_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_request_bot, pattern="^request_bot$")],
        states={
            REQUEST_WAITING_PAYMENT: [
                CallbackQueryHandler(handle_payment_creation, pattern="^pay_subscription$"),
                CallbackQueryHandler(check_payment_status, pattern="^check_payment$"),
                CallbackQueryHandler(handle_pago_movil_selection, pattern="^pay_pago_movil$"),
                CallbackQueryHandler(confirm_pago_movil, pattern="^confirm_pago_movil$"),
                CallbackQueryHandler(start_request_bot, pattern="^(request_bot|start_request_bot_back)$"),
                CallbackQueryHandler(cancel_request, pattern="^request_cancel$")
            ],
            REQUEST_WAITING_REFERENCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_pago_movil_reference),
                CallbackQueryHandler(cancel_request, pattern="^request_cancel$")
            ],
            REQUEST_WAITING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_full_name),
                CallbackQueryHandler(cancel_request, pattern="^request_cancel$")
            ],
            REQUEST_WAITING_TELEGRAM_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_telegram_id),
                CallbackQueryHandler(cancel_request, pattern="^request_cancel$")
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel_request, pattern="^(request_cancel|main_menu)$")],
        name="request_bot_conversation",
        persistent=True,
    )
    # ⚠️ Este handler debe registrarse ANTES de handlers genéricos de mensajes
    application.add_handler(request_bot_conv)
    
    # ConversationHandler para edición de contacto
    contact_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_contact_edit, pattern="^contact_edit_"),
            CallbackQueryHandler(show_contact_menu, pattern="^contacto_menu$"),
        ],
        states={
            CONTACT_WAITING_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_contact_value),
                CallbackQueryHandler(cancel_contact_edit, pattern="^contact_cancel$")
            ]
        },
        fallbacks=[CallbackQueryHandler(cancel_contact_edit, pattern="^contact_cancel$")],
        name="contact_conversation",
        persistent=True
    )
    application.add_handler(contact_conv_handler)
    
    # ConversationHandler para agendar citas (paciente)
    booking_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_booking, pattern="^patient_book_appointment$")],
        states={
            AWAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            SELECTING_CONSULTATION_TYPE: [
                CallbackQueryHandler(handle_consultation_type, pattern="^book_consult_type_")
            ],
            AWAITING_PREGNANCY_INFO: [
                CallbackQueryHandler(handle_pregnancy_info, pattern="^book_(first|ever)_preg_")
            ],
            AWAITING_REASON: [
                CallbackQueryHandler(handle_reason, pattern="^book_reason_")
            ],
            SELECTING_LOCATION: [CallbackQueryHandler(handle_location, pattern="^book_loc_")],
            SELECTING_DATE: [
                CallbackQueryHandler(calendar_handler_booking, pattern="^book_cal_"),
                CallbackQueryHandler(back_to_locations, pattern="^book_back_to_locations$")
            ],
            SELECTING_TIME: [
                CallbackQueryHandler(handle_time, pattern="^book_time_"),
                CallbackQueryHandler(calendar_handler_booking, pattern="^book_back_to_calendar$")
            ],
            CONFIRMING: [
                CallbackQueryHandler(confirm_appointment, pattern="^book_confirm_yes$"),
                CallbackQueryHandler(back_to_locations, pattern="^book_back_to_locations$")
            ],
            FINAL_STATE: [CallbackQueryHandler(back_to_main_menu, pattern="^book_back_to_main_menu$")]
        },
        fallbacks=[
            CallbackQueryHandler(back_to_main_menu, pattern="^main_menu$"),
            CallbackQueryHandler(cancel_booking, pattern="^book_cancel$")
        ],
        name="booking_conversation",
        persistent=True,
        allow_reentry=True
    )
    application.add_handler(booking_conv)

    # Registrar ConversationHandler de preconsulta
    from features.preconsulta.main_handler import register as register_preconsulta
    register_preconsulta(application)
    
    # Registrar handlers de administración de citas (incluye botones Recuérdame y Descartar)
    from features.citas.admin_handlers import register as register_citas_admin_handlers
    register_citas_admin_handlers(application)
    
    from features.citas.admin_manual_booking import register as register_admin_manual_booking
    register_admin_manual_booking(application)
    
    # Registrar handlers de gestión de preconsultas (Gestión Historia)
    from features.preconsultas_admin.admin_handlers import register as register_preconsultas_admin
    register_preconsultas_admin(application)
    
    # Registrar handlers de archivo de pacientes (búsqueda y edición)
    from features.preconsulta.patient_archive.admin_handlers import register as register_patient_archive
    register_patient_archive(application)
    
    # Registrar handlers de configuración de PDF
    from features.pdf_configuration.handlers import register as register_pdf_configuration
    register_pdf_configuration(application)

    # Handler central de callbacks (debe ir al final)
    # ⚠️ IMPORTANTE: Los callbacks del test son manejados por el ConversationHandler
    # El ConversationHandler del test debe estar registrado ANTES de este handler
    # Si un callback del test llega aquí, handle_all_callbacks lo ignorará
    application.add_handler(CallbackQueryHandler(handle_all_callbacks))

