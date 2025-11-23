"""
Handlers de menús principales.
Interacción con Telegram para mostrar menús.
"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from features.main_menu.keyboards import get_main_menu_keyboard
from ..views.keyboards import get_doctors_management_keyboard
from ..views.messages import format_doctors_menu_text
from ..utils import safe_edit_message


async def superadmin_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú principal para SuperAdmin"""
    print("🔄 Mostrando menú superadmin")
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        texto = "🏠 **Menú Principal - SuperAdmin**\n\nSelecciona una opción:"
        keyboard = await get_main_menu_keyboard(is_superadmin=True)
        
        try:
            await query.edit_message_text(
                texto,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except BadRequest as e:
            # Si el mensaje es una foto (no tiene texto), eliminar primero
            if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
                try:
                    await query.message.delete()
                except:
                    pass
                # Luego enviar nuevo mensaje con texto y botones
                await context.bot.send_message(
                    chat_id=query.message.chat.id,
                    text=texto,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            else:
                # Otro error, enviar nuevo mensaje
                await context.bot.send_message(
                    chat_id=query.message.chat.id,
                    text=texto,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
    else:
        keyboard = await get_main_menu_keyboard(is_superadmin=True)
        await update.message.reply_text(
            "🏠 **Menú Principal - SuperAdmin**\n\nSelecciona una opción:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


async def show_doctors_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el submenú de gestión de médicos"""
    query = update.callback_query
    await query.answer()
    print("🔄 Mostrando menú de médicos")
    
    texto = format_doctors_menu_text()
    keyboard = get_doctors_management_keyboard()
    
    await safe_edit_message(query, texto, keyboard, context)

