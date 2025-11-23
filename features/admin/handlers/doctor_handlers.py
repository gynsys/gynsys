"""
Handlers de gestión de médicos.
Incluye flujos de alta/baja (ConversationHandler) y acciones directas.
"""
import asyncio
import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from features.doctors.management_handler import doctors_management
from ..services.admin_service import AdminService
from ..views.keyboards import (
    get_doctors_management_keyboard,
    get_back_to_doctors_keyboard,
    get_doctors_list_keyboard,
    get_delete_doctors_keyboard,
    get_restrict_doctors_keyboard,
    get_permit_doctors_keyboard,
)
from ..views.messages import (
    format_add_doctor_prompt_name,
    format_add_doctor_prompt_id,
    format_add_doctor_invalid_id,
    format_doctor_added_success,
    format_doctor_add_error,
    format_doctor_list,
    format_doctor_delete_success,
    format_doctor_restrict_success,
    format_doctor_permit_success,
    format_doctors_menu_text,
    format_delete_menu_text,
    format_restrict_menu_text,
    format_permit_menu_text,
    format_welcome_notification,
    format_cancel_add_doctor,
)
from ..utils import paginate, safe_edit_message
from ..views.keyboards import get_back_to_main_keyboard

# Estados para la conversación de agregar médico
WAITING_FOR_DOCTOR_NAME = 1
WAITING_FOR_DOCTOR_ID = 2

# Instancia del servicio
admin_service = AdminService()


async def start_add_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso para agregar un nuevo médico"""
    query = update.callback_query
    await query.answer()
    print("🔄 Iniciando proceso de agregar médico")
    
    # Guardar el ID del mensaje para poder editarlo después
    context.user_data['last_message_id'] = query.message.message_id
    context.user_data['return_to'] = 'doctors_menu'
    
    await context.bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=format_add_doctor_prompt_name(),
        parse_mode="Markdown"
    )
    
    return WAITING_FOR_DOCTOR_NAME


async def receive_doctor_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el nombre del médico y pide el ID de Telegram"""
    print(f"🔄 Recibiendo nombre del médico: {update.message.text}")
    doctor_name = update.message.text.strip()
    context.user_data['new_doctor_name'] = doctor_name
    
    # Eliminar mensaje del usuario para mantener limpio
    await update.message.delete()
    
    # Editar el mensaje anterior para pedir el ID
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data.get('last_message_id'),
        text=format_add_doctor_prompt_id(doctor_name),
        parse_mode="Markdown"
    )
    
    return WAITING_FOR_DOCTOR_ID


async def receive_doctor_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el ID de Telegram del médico y lo guarda en el sistema"""
    print(f"🔄 Recibiendo ID del médico: {update.message.text}")
    doctor_id_text = update.message.text.strip()
    
    # Validar que sea un número
    if not doctor_id_text.isdigit():
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=context.user_data.get('last_message_id'),
            text=format_add_doctor_invalid_id(),
            parse_mode="Markdown"
        )
        return WAITING_FOR_DOCTOR_ID
    
    telegram_id = int(doctor_id_text)
    doctor_name = context.user_data.get('new_doctor_name')
    
    # Eliminar mensaje del usuario
    await update.message.delete()
    
    try:
        # Agregar o reactivar médico
        doctor_id, is_new = await admin_service.add_or_reactivate_doctor(doctor_name, telegram_id)
        
        # Inicializar datos por defecto si es nuevo
        if is_new:
            bot_id = await admin_service.get_bot_id_for_doctor(telegram_id)
            if bot_id:
                await admin_service.initialize_tenant_data(bot_id, doctor_name)
        
        # Generar código de compartir y enlace
        bot_username = update.effective_user.username or context.bot.username or "<tu_bot>"
        share_code, deeplink = admin_service.generate_share_info(doctor_id, bot_username)
        
        # Enviar notificación push al nuevo doctor
        try:
            welcome_text = format_welcome_notification(deeplink, share_code)
            await context.bot.send_message(
                chat_id=telegram_id,
                text=welcome_text,
                parse_mode="HTML",
            )
        except Exception as e:
            # Si no se puede enviar el mensaje, solo lo registramos
            admin_service.logger.warning(f"No se pudo enviar notificación a {telegram_id}: {e}")
        
        # Mostrar mensaje de éxito
        success_text = format_doctor_added_success(doctor_name, telegram_id, deeplink, share_code)
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=context.user_data.get('last_message_id'),
            text=success_text,
            parse_mode="Markdown"
        )
        
        # Esperar 3 segundos para que el usuario lea el mensaje
        await asyncio.sleep(3)
        
        # Regresar automáticamente al submenú de médicos
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=context.user_data.get('last_message_id'),
            text=format_doctors_menu_text(),
            reply_markup=get_doctors_management_keyboard(),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        # En caso de error
        error_text = format_doctor_add_error(str(e))
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=context.user_data.get('last_message_id'),
            text=error_text,
            parse_mode="Markdown",
            reply_markup=get_back_to_doctors_keyboard()
        )
    
    # Limpiar datos temporales
    context.user_data.pop('new_doctor_name', None)
    context.user_data.pop('last_message_id', None)
    context.user_data.pop('return_to', None)
    
    return ConversationHandler.END


async def cancel_add_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela el proceso de agregar médico"""
    print("🔄 Cancelando proceso de agregar médico")
    # Limpiar datos temporales
    doctor_name = context.user_data.pop('new_doctor_name', None)
    last_message_id = context.user_data.pop('last_message_id', None)
    return_to = context.user_data.pop('return_to', 'doctors_menu')
    
    cancel_text = format_cancel_add_doctor()
    keyboard = get_doctors_management_keyboard() if return_to == 'doctors_menu' else get_back_to_main_keyboard()
    
    if last_message_id:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=last_message_id,
            text=cancel_text,
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            cancel_text,
            reply_markup=keyboard
        )
    
    return ConversationHandler.END


async def show_doctors_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra lista simple de médicos registrados"""
    query = update.callback_query
    await query.answer()
    print("🔄 Mostrando lista de médicos")
    
    try:
        doctors = await admin_service.get_all_doctors()
        
        if not doctors:
            texto = format_doctor_list(doctors)
            keyboard = get_back_to_doctors_keyboard()
            await safe_edit_message(query, texto, keyboard, context)
            return
        
        text = format_doctor_list(doctors)
        keyboard = get_doctors_list_keyboard(doctors)
        
        await safe_edit_message(query, text, keyboard, context, parse_mode="HTML")
        
    except Exception as e:
        print(f"❌ Error mostrando lista de médicos: {e}")
        await query.edit_message_text(
            "❌ **Error al cargar la lista de médicos**",
            reply_markup=get_back_to_doctors_keyboard()
        )


async def show_delete_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Muestra menú para eliminar médicos con paginación"""
    query = update.callback_query
    await query.answer()
    
    doctors = await admin_service.get_all_doctors()
    if not doctors:
        texto = "🗑️ No hay médicos activos para eliminar."
        keyboard = get_back_to_doctors_keyboard()
        await safe_edit_message(query, texto, keyboard, context)
        return
    
    slice_docs, page, total_pages = paginate(doctors, page)
    text = format_delete_menu_text(page, total_pages)
    
    # Agregar lista de médicos
    for doctor in slice_docs:
        text += f"• {doctor[1]} (ID: {doctor[2]})\n"
    
    keyboard = get_delete_doctors_keyboard(slice_docs, page, total_pages)
    await safe_edit_message(query, text, keyboard, context, parse_mode="HTML")


async def show_simple_restrict_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Muestra menú para restringir médicos con paginación"""
    query = update.callback_query
    await query.answer()
    
    doctors = await admin_service.get_all_doctors()
    if not doctors:
        texto = "🔒 No hay médicos activos para restringir."
        keyboard = get_back_to_doctors_keyboard()
        await safe_edit_message(query, texto, keyboard, context)
        return
    
    slice_docs, page, total_pages = paginate(doctors, page)
    text = format_restrict_menu_text(page, total_pages)
    
    keyboard = get_restrict_doctors_keyboard(slice_docs, page, total_pages)
    await safe_edit_message(query, text, keyboard, context, parse_mode="HTML")


async def show_simple_permit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Muestra menú para permitir médicos con paginación"""
    query = update.callback_query
    await query.answer()
    
    doctors = await admin_service.get_inactive_doctors()
    if not doctors:
        texto = "🔓 No hay médicos restringidos."
        keyboard = get_back_to_doctors_keyboard()
        await safe_edit_message(query, texto, keyboard, context)
        return
    
    slice_docs, page, total_pages = paginate(doctors, page)
    text = format_permit_menu_text(page, total_pages)
    
    keyboard = get_permit_doctors_keyboard(slice_docs, page, total_pages)
    await safe_edit_message(query, text, keyboard, context, parse_mode="HTML")


async def simple_delete_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE, doctor_id: int):
    """Elimina un médico permanentemente"""
    query = update.callback_query
    await query.answer()
    
    doctor = await admin_service.get_doctor_by_id(doctor_id)
    if not doctor:
        await query.edit_message_text(
            "⚠️ No se encontró el médico seleccionado.",
            reply_markup=get_back_to_doctors_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    result = await admin_service.remove_doctor_permanently(doctor_id)
    
    if result:
        success_text = format_doctor_delete_success(doctor[1], doctor[2])
        await query.edit_message_text(
            success_text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Volver", callback_data="delete_doctor_menu")]]),
            parse_mode="HTML"
        )
        # Refrescar la lista después de un breve delay
        await asyncio.sleep(1.5)
        await show_delete_menu(update, context, page=0)
    else:
        await query.edit_message_text(
            "❌ Error al eliminar el médico. Por favor, intenta nuevamente.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Volver", callback_data="delete_doctor_menu")]]),
            parse_mode="HTML"
        )


async def simple_restrict_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE, doctor_id: int):
    """Restringe un médico"""
    query = update.callback_query
    await query.answer()
    
    doctor = await admin_service.get_doctor_by_id(doctor_id)
    if not doctor:
        await query.edit_message_text(
            "⚠️ No se encontró el médico seleccionado.",
            reply_markup=get_back_to_doctors_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    await admin_service.restrict_doctor(doctor_id)
    success_text = format_doctor_restrict_success(doctor[1], doctor[2])
    await query.edit_message_text(
        success_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Volver", callback_data="simple_restrict_menu")]]),
        parse_mode="HTML"
    )


async def simple_permit_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE, doctor_id: int):
    """Permite/reactiva un médico"""
    query = update.callback_query
    await query.answer()
    
    doctor = await admin_service.get_doctor_by_id(doctor_id)
    if not doctor:
        await query.edit_message_text(
            "⚠️ No se encontró el médico seleccionado.",
            reply_markup=get_back_to_doctors_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    await admin_service.activate_doctor(doctor_id)
    success_text = format_doctor_permit_success(doctor[1], doctor[2])
    await query.edit_message_text(
        success_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Volver", callback_data="simple_permit_menu")]]),
        parse_mode="HTML"
    )


async def show_restrict_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la gestión de médicos para restringir/eliminar"""
    query = update.callback_query
    await query.answer()
    print("🔄 Mostrando gestión de médicos")
    
    await doctors_management.show_doctors_management(update, context, page=0)

