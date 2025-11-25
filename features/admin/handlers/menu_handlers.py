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
from common.helpers import cleanup_extra_messages

async def superadmin_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra el menú principal para SuperAdmin, asegurando la limpieza de mensajes previos.
    """
    # 1. LIMPIEZA PRIMERO, sin importar si es callback o mensaje
    # Esta es la corrección principal para solucionar el problema de la galería.
    await cleanup_extra_messages(context, update.effective_chat.id)

    print("🔄 Mostrando menú superadmin")
    
    # 2. PREPARAMOS EL CONTENIDO DEL MENÚ
    texto = "🏠 **Menú Principal - SuperAdmin**\n\nSelecciona una opción:"
    keyboard = await get_main_menu_keyboard(is_superadmin=True)
    
    # 3. LÓGICA DE ENVÍO/EDICIÓN UNIFICADA Y ROBUSTA
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        try:
            # Intentamos editar el mensaje del botón presionado
            await query.edit_message_text(
                texto,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except BadRequest as e:
            # Si la edición falla porque el mensaje no se puede editar o no existe,
            # simplemente enviamos uno nuevo. Esto cubre todos los casos de error.
            if "Message is not modified" not in str(e):
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=texto,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
    
    # Si el update no es un callback_query (ej. /start), siempre enviamos un mensaje nuevo.
    elif update.message:
        await update.message.reply_text(
            texto,
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

