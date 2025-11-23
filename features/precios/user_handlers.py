# /features/precios/user_handlers.py
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest
from database import content_db
from common import texts
from common.keyboards import get_back_to_menu_keyboard
from common.context_manager import get_tenant_id
from .keyboards import get_precios_keyboard

async def show_precios_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await query.answer("❌ Error al obtener información.", show_alert=True)
        return
    
    texto = await texts.get_texto('header_precios', bot_id, '💰 Inversión en tu Salud')
    reply_markup = await get_precios_keyboard(bot_id)
    
    # Manejar transición desde mensaje con imagen
    try:
        await query.edit_message_text(text=texto, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=texto,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )

async def show_precio_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    item_id = int(query.data.split('_')[-1])
    texto = await content_db.get_item_content(item_id, 'content', table_name='precios')
    if not texto:
        texto = "❌ Contenido no encontrado."
    
    # Obtener bot_id para el callback de volver
    bot_id = await get_tenant_id(update, context)
    back_callback = 'precios_menu' if bot_id else 'main_menu'
    
    try:
        await query.edit_message_text(
            text=texto,
            reply_markup=get_back_to_menu_keyboard(back_callback),
            parse_mode=ParseMode.HTML
        )
    except BadRequest as e:
        if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=texto,
                reply_markup=get_back_to_menu_keyboard(back_callback),
                parse_mode=ParseMode.HTML
            )

def register(app: Application):
    app.add_handler(CallbackQueryHandler(show_precios_menu, pattern='^precios$'))
    app.add_handler(CallbackQueryHandler(show_precio_content, pattern='^precio_item_'))