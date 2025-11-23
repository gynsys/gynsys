"""
Handlers de solicitudes de médicos.
Interacción con Telegram para aprobar/rechazar solicitudes.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from ..services.request_service import RequestService
from ..services.admin_service import AdminService
from ..views.keyboards import get_requests_list_keyboard, get_request_detail_keyboard
from ..views.messages import (
    format_request_list,
    format_request_detail,
    format_request_approved,
    format_request_rejected,
    format_welcome_notification,
)
from ..utils import safe_edit_message

# Instancias de servicios
request_service = RequestService()
admin_service = AdminService()


async def show_requests_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú de solicitudes pendientes"""
    query = update.callback_query
    await query.answer()
    
    pending = await request_service.list_pending()
    
    text = format_request_list(pending)
    keyboard = get_requests_list_keyboard(pending) if pending else InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Inicio", callback_data="main_menu")]
    ])
    
    await safe_edit_message(query, text, keyboard, context)


async def show_request_detail(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int):
    """Muestra el detalle de una solicitud"""
    query = update.callback_query
    await query.answer()
    
    request = await request_service.get_request_by_id(request_id)
    if not request or request["status"] != "pending":
        await query.edit_message_text(
            "⚠️ La solicitud ya no está disponible.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Solicitudes", callback_data="requests_menu")]]),
            parse_mode="Markdown"
        )
        return
    
    text = format_request_detail(request)
    keyboard = get_request_detail_keyboard(request_id)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


async def approve_request(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int):
    """Aprueba una solicitud de médico"""
    query = update.callback_query
    await query.answer()
    
    # Verificar que la solicitud existe y está pendiente
    request = await request_service.get_request_by_id(request_id)
    if not request or request["status"] != "pending":
        await query.edit_message_text(
            "⚠️ La solicitud ya fue procesada.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Solicitudes", callback_data="requests_menu")]]),
            parse_mode="Markdown"
        )
        return
    
    # Aprobar solicitud (crea/reactiva médico)
    result = await request_service.approve_request(request_id, admin_service)
    if not result:
        await query.edit_message_text(
            "⚠️ Error al procesar la solicitud.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Solicitudes", callback_data="requests_menu")]]),
            parse_mode="Markdown"
        )
        return
    
    doctor_id, full_name, telegram_id = result
    
    # Generar información de compartir
    bot_username = context.bot.username or "<tu_bot>"
    share_code, deeplink = request_service.generate_share_info(doctor_id, bot_username)
    
    # Mostrar mensaje de éxito
    success_text = format_request_approved(full_name, telegram_id, deeplink, share_code)
    await query.edit_message_text(
        success_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Solicitudes", callback_data="requests_menu")]]),
        parse_mode="HTML"
    )
    
    # Enviar notificación al médico
    try:
        welcome_text = format_welcome_notification(deeplink, share_code)
        await context.bot.send_message(
            chat_id=telegram_id,
            text=welcome_text,
            parse_mode="HTML",
        )
    except Exception as exc:
        admin_service.logger.warning(f"No se pudo notificar al médico {telegram_id}: {exc}")


async def reject_request(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int):
    """Rechaza/pospone una solicitud de médico"""
    query = update.callback_query
    await query.answer()
    
    # Verificar que la solicitud existe y está pendiente o diferida
    request = await request_service.get_request_by_id(request_id)
    if not request or request["status"] not in {"pending", "deferred"}:
        await query.edit_message_text(
            "⚠️ La solicitud ya fue procesada.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Solicitudes", callback_data="requests_menu")]]),
            parse_mode="Markdown"
        )
        return
    
    # Rechazar solicitud
    await request_service.reject_request(request_id)
    
    # Mostrar mensaje de éxito
    success_text = format_request_rejected()
    await query.edit_message_text(
        success_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Solicitudes", callback_data="requests_menu")]]),
        parse_mode="Markdown"
    )

