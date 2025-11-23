"""
Templates de mensajes para el módulo admin.
Textos largos y templates (f-strings) para presentación.
"""
import html


def format_doctor_added_success(doctor_name, telegram_id, deeplink, share_code):
    """
    Formatea el mensaje de éxito al agregar un médico.
    """
    return (
        f"✅ **Médico agregado exitosamente!**\n\n"
        f"👨‍⚕️ **Nombre:** {doctor_name}\n"
        f"🆔 **ID de Telegram:** {telegram_id}\n\n"
        f"🔗 **Enlace:** {deeplink}\n"
        f"📛 **Código:** `{share_code}`\n\n"
        "Se ha enviado una notificación al médico con su enlace.\n\n"
        "Redirigiendo al menú de médicos..."
    )


def format_doctor_add_error(error_msg):
    """
    Formatea el mensaje de error al agregar un médico.
    """
    if "UNIQUE constraint failed" in error_msg:
        error_msg = "El ID de Telegram ya está registrado en el sistema."
    
    return (
        f"❌ **Error al agregar médico**\n\n"
        f"Error: {error_msg}\n\n"
        f"Por favor, intenta nuevamente."
    )


def format_doctor_list(doctors, page=0, total_pages=1):
    """
    Formatea la lista de médicos.
    
    Args:
        doctors: Lista de tuplas (id, name, telegram_id)
        page: Página actual (0-indexed)
        total_pages: Total de páginas
    """
    if not doctors:
        return "📋 **Lista de Médicos**\n\nNo hay médicos registrados en el sistema."
    
    text = "📋 <b>Listado de Médicos</b>\n────────────────────\n"
    for i, doctor in enumerate(doctors, 1):
        text += f"{i}. 👨‍⚕️ {doctor[1]} (ID: {doctor[2]})\n"
    
    return text


def format_doctor_delete_success(doctor_name, doctor_telegram_id):
    """
    Formatea el mensaje de éxito al eliminar un médico.
    """
    return f"🗑️ Se eliminó al médico {doctor_name} (ID: {doctor_telegram_id})."


def format_doctor_restrict_success(doctor_name, doctor_telegram_id):
    """
    Formatea el mensaje de éxito al restringir un médico.
    """
    return f"🔒 Se restringió al médico {doctor_name} (ID: {doctor_telegram_id})."


def format_doctor_permit_success(doctor_name, doctor_telegram_id):
    """
    Formatea el mensaje de éxito al permitir un médico.
    """
    return f"🔓 Se reactivó al médico {doctor_name} (ID: {doctor_telegram_id})."


def format_doctors_menu_text():
    """
    Texto del menú de gestión de médicos.
    """
    return (
        "👨‍⚕️ **Gestión de Médicos**\n\n"
        "Selecciona una opción para gestionar los médicos del sistema:"
    )


def format_delete_menu_text(page=0, total_pages=1):
    """
    Texto del menú de eliminar médicos.
    """
    return f"🗑️ <b>Eliminar un Médico</b>\nPágina {page + 1}/{total_pages}\n\n"


def format_restrict_menu_text(page=0, total_pages=1):
    """
    Texto del menú de restringir médicos.
    """
    return f"🔒 <b>Restringir acceso</b>\nPágina {page + 1}/{total_pages}\n\n"


def format_permit_menu_text(page=0, total_pages=1):
    """
    Texto del menú de permitir médicos.
    """
    return f"🔓 <b>Permitir acceso</b>\nPágina {page + 1}/{total_pages}\n\n"


def format_request_list(requests):
    """
    Formatea la lista de solicitudes.
    
    Args:
        requests: Lista de diccionarios con 'full_name' y 'telegram_id'
    """
    if not requests:
        return "🆕 **Solicitudes de Médicos**\n\nNo hay solicitudes pendientes."
    
    text = "🆕 **Solicitudes Pendientes**\n\n"
    for idx, req in enumerate(requests, start=1):
        text += f"{idx}. {req['full_name']} (ID: {req['telegram_id']})\n"
    
    return text


def format_request_detail(request):
    """
    Formatea el detalle de una solicitud.
    
    Args:
        request: Diccionario con datos de la solicitud
    """
    estado = "Pendiente" if request["status"] == "pending" else "Pospuesta"
    return (
        "📝 <b>Solicitud de Médico</b>\n\n"
        f"<b>Estado:</b> {estado}\n"
        f"<b>Nombre:</b> {html.escape(request['full_name'])}\n"
        f"<b>Telegram ID:</b> {request['telegram_id']}\n"
        f"<b>Fecha:</b> {request['created_at']}\n"
    )


def format_request_approved(full_name, telegram_id, deeplink, share_code):
    """
    Formatea el mensaje de solicitud aprobada.
    """
    return (
        "✅ <b>Solicitud aprobada</b>\n\n"
        f"<b>Nombre:</b> {html.escape(full_name)}\n"
        f"<b>Telegram ID:</b> {telegram_id}\n\n"
        f"🔗 Enlace: {html.escape(deeplink)}\n"
        f"📛 Código: <code>{share_code}</code>"
    )


def format_request_rejected():
    """
    Formatea el mensaje de solicitud rechazada/pospuesta.
    """
    return "🕓 Solicitud pospuesta. Podrás procesarla más adelante desde el panel de solicitudes."


def format_welcome_notification(deeplink, share_code):
    """
    Formatea el mensaje de bienvenida para el nuevo médico.
    """
    return (
        "👋 <b>¡Bienvenido a GynSys!</b>\n\n"
        f"Tu bot está listo.\n\n🔗 Enlace: {html.escape(deeplink)}\n"
        f"📛 Código: <code>{share_code}</code>\n"
        "Compártelo con tus pacientes para que se conecten contigo."
    )


def format_add_doctor_prompt_name():
    """
    Mensaje para pedir el nombre del médico.
    """
    return (
        "👨‍⚕️ **Agregar Nuevo Médico**\n\n"
        "Por favor, envía el *nombre* del nuevo médico:\n\n"
        "❌ *Para cancelar escribe:* /cancel"
    )


def format_add_doctor_prompt_id(doctor_name):
    """
    Mensaje para pedir el ID de Telegram del médico.
    """
    return (
        f"✅ **Nombre recibido:** {doctor_name}\n\n"
        "Ahora envía el *ID de Telegram* del médico:\n\n"
        "🔍 *Cómo obtener el ID:*\n"
        "1. Pídele al médico que escriba @userinfobot en Telegram\n"
        "2. El bot le mostrará su ID numérico\n"
        "3. Que te envíe ese número\n\n"
        "❌ *Para cancelar escribe:* /cancel"
    )


def format_add_doctor_invalid_id():
    """
    Mensaje de error cuando el ID es inválido.
    """
    return (
        "❌ **ID inválido**\n\n"
        "El ID de Telegram debe ser un número.\n"
        "Por favor, envía un ID válido:"
    )


def format_cancel_add_doctor():
    """
    Mensaje de cancelación al agregar médico.
    """
    return "❌ **Operación cancelada**\n\nNo se agregó ningún médico al sistema."

