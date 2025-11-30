# features/precios/admin_handlers.py
import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, ConversationHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, CommandHandler

from database import content_db
from common.decorators import admin_required
from common.helpers import escape_html
from common.keyboards import get_delete_confirmation_keyboard
from common.conversation_utils import cancel_conv
from common.context_manager import get_tenant_id

from . import keyboards as admin_keyboards

logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN Y ESTADOS ---
CONFIG = {'singular': 'Precio', 'plural': 'Precios', 'table': 'precios', 'title_col': 'title', 'content_col': 'content', 'prefix': 'precio'}
(AWAITING_TITLE, AWAITING_CONTENT, AWAITING_MOD_TITLE, AWAITING_MOD_CONTENT, AWAITING_HEADER_TEXT) = range(5)

# --- HUB DE GESTIÓN ---
@admin_required
async def prices_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    
    # Determinar callback de retorno según rol
    user_id = update.effective_user.id
    from config import SUPER_ADMIN_ID
    back_callback = 'doctor_panel'
    # Si es superadmin, también volvemos al doctor_panel (que debe ser manejado por el router)
    # o al menú principal si no está impersonando (pero asumimos que quiere ver el panel)
    
    keyboard = [
        # [InlineKeyboardButton(f"✏️ Editar Encabezado", callback_data=f"{CONFIG['prefix']}_edit_header")],

        [InlineKeyboardButton(f"➕ Añadir {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_add_start")],
        [InlineKeyboardButton(f"✏️ Modificar {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_modify_list")],
        [InlineKeyboardButton(f"🗑️ Eliminar {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_delete_list")],
        [InlineKeyboardButton("🔙 Volver", callback_data=back_callback), InlineKeyboardButton("🏠 Menú Principal", callback_data='main_menu')]
    ]
    await query.edit_message_text(f"🔧 <b>Gestión de {CONFIG['plural']}</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

# --- LÓGICA CRUD ---
@admin_required
async def list_items_for_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    action = query.data.split('_')[1]
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await query.answer("❌ No se pudo obtener el tenant ID.", show_alert=True)
        return
    reply_markup = await admin_keyboards.get_precios_for_action_keyboard(bot_id, action)
    if not reply_markup:
        await query.answer(f"No hay {CONFIG['plural'].lower()} para gestionar.", show_alert=True); return
    action_text = 'modificar' if action == 'modify' else 'eliminar'
    await query.edit_message_text(f"Selecciona el {CONFIG['singular'].lower()} que deseas {action_text}:", reply_markup=reply_markup, parse_mode="HTML")

@admin_required
async def confirm_delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    item_id = int(query.data.split('_')[-1])
    item_details = await content_db.get_item_details(item_id, CONFIG['table'], CONFIG['title_col'], CONFIG['content_col'])
    item_name = item_details.get('title', 'este elemento') if item_details else 'este elemento'
    callback_for_confirmation = f"{CONFIG['prefix']}_delete_execute_confirm_{item_id}"
    await query.edit_message_text(f"<b>⚠️ ¿Seguro que quieres eliminar?</b>\n\n<blockquote>{escape_html(item_name)}</blockquote>",
        reply_markup=get_delete_confirmation_keyboard(item_type_callback=callback_for_confirmation, back_callback=f"{CONFIG['prefix']}_delete_list"))

@admin_required
async def execute_delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    item_id = int(query.data.split('_')[-1])
    if await content_db.delete_item(item_id, CONFIG['table']):
        await query.answer("✅ Elemento eliminado.", show_alert=True)
    fake_query = type('obj', (object,), {'data': f"{CONFIG['prefix']}_delete_list", 'message': query.message, 'answer': lambda *a, **k: asyncio.sleep(0), 'edit_message_text': query.message.edit_text})()
    fake_update = type('obj', (object,), {'callback_query': fake_query, 'effective_user': update.effective_user})()
    await list_items_for_action(fake_update, context)

@admin_required

# --- CONVERSATION HANDLERS ---
@admin_required
async def start_header_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await query.answer("❌ No se pudo obtener el tenant ID.", show_alert=True)
        return ConversationHandler.END
    header_key = "header_precios"
    context.user_data.update({'header_key_to_edit': header_key, 'main_conv_message_id': query.message.message_id})
    current_header = await content_db.get_content(header_key, bot_id) or "(Sin encabezado definido)"
    await query.edit_message_text(f"✍️ Editando encabezado para <b>{CONFIG['plural']}</b>\n\n<b>Texto actual:</b>\n<blockquote>{escape_html(current_header)}</blockquote>\n\nEnvía el nuevo texto.\n\n<i>/cancelar para detener.</i>", parse_mode="HTML")
    return AWAITING_HEADER_TEXT

async def save_modified_header(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_header = update.message.text_html; await update.message.delete()
    header_key = context.user_data.pop('header_key_to_edit')
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await update.message.reply_text("❌ Error: No se pudo obtener el tenant ID.")
        return ConversationHandler.END
    await content_db.update_content(header_key, new_header, bot_id)
    message_to_edit = await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data.pop('main_conv_message_id'), text="✅ Encabezado actualizado.")
    await asyncio.sleep(2)
    fake_query = type('obj', (object,), {'data': 'prices_admin_hub', 'message': message_to_edit, 'answer': lambda *a, **k: asyncio.sleep(0), 'edit_message_text': message_to_edit.edit_text})()
    fake_update = type('obj', (object,), {'callback_query': fake_query, 'effective_user': update.effective_user, 'effective_chat': update.effective_chat})()
    await prices_hub(fake_update, context)
    return ConversationHandler.END

@admin_required
async def add_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    context.user_data['main_conv_message_id'] = query.message.message_id
    await query.edit_message_text(f"✍️ Envía el <b>título</b> para el nuevo {CONFIG['singular']}.\n\n<i>/cancelar para detener.</i>", parse_mode="HTML")
    return AWAITING_TITLE

async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['item_title'] = update.message.text; await update.message.delete()
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['main_conv_message_id'], text="✅ Título guardado. Ahora, envía el <b>contenido</b>.", parse_mode="HTML")
    return AWAITING_CONTENT

async def save_new_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    title = context.user_data.pop('item_title'); content = update.message.text_html
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await update.message.reply_text("❌ Error: No se pudo obtener el tenant ID.")
        return ConversationHandler.END
    await content_db.add_item(bot_id, CONFIG['table'], title, content, CONFIG['title_col'], CONFIG['content_col'])
    await update.message.delete()
    message_to_edit = await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data.pop('main_conv_message_id'), text=f"✅ ¡{CONFIG['singular']} añadido con éxito!")
    await asyncio.sleep(2)
    fake_query = type('obj', (object,), {'message': message_to_edit, 'answer': lambda *a, **k: asyncio.sleep(0), 'edit_message_text': message_to_edit.edit_text})()
    fake_update = type('obj', (object,), {'callback_query': fake_query, 'effective_user': update.effective_user})()
    await prices_hub(fake_update, context)
    return ConversationHandler.END

@admin_required
async def modify_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    item_id = int(query.data.split('_')[-1])
    item_details = await content_db.get_item_details(item_id, CONFIG['table'], CONFIG['title_col'], CONFIG['content_col'])
    if not item_details: return ConversationHandler.END
    context.user_data.update({'item_id_to_modify': item_id, 'original_item': item_details, 'main_conv_message_id': query.message.message_id})
    await query.edit_message_text(f"✏️ Modificando '{item_details['title']}'.\n\n<b>Título actual:</b>\n<blockquote>{escape_html(item_details['title'])}</blockquote>\nEnvía el <b>nuevo título</b> o '.' para mantener.\n\n<i>/cancelar para detener.</i>", parse_mode="HTML")
    return AWAITING_MOD_TITLE

async def receive_modified_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != '.': context.user_data['new_title'] = update.message.text
    await update.message.delete()
    original_item = context.user_data['original_item']
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['main_conv_message_id'],
        text=f"<b>Contenido actual:</b>\n<blockquote>{escape_html(original_item['content'])}</blockquote>\nEnvía el <b>nuevo contenido</b> o '.' para mantener.", parse_mode="HTML")
    return AWAITING_MOD_CONTENT

async def save_modified_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text_html != '.': context.user_data['new_content'] = update.message.text_html
    await update.message.delete()
    ud = context.user_data; original_item = ud.pop('original_item'); item_id = ud.pop('item_id_to_modify')
    final_title = ud.get('new_title', original_item['title']); final_content = ud.get('new_content', original_item['content'])
    await content_db.update_item(item_id, CONFIG['table'], final_title, final_content, CONFIG['title_col'], CONFIG['content_col'])
    message_to_edit = await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=ud.pop('main_conv_message_id'), text=f"✅ ¡{CONFIG['singular']} actualizado con éxito!")
    await asyncio.sleep(2)
    fake_query = type('obj', (object,), {'data': f"{CONFIG['prefix']}_modify_list", 'message': message_to_edit, 'answer': lambda *a, **k: asyncio.sleep(0), 'edit_message_text': message_to_edit.edit_text})()
    fake_update = type('obj', (object,), {'callback_query': fake_query, 'effective_user': update.effective_user})()
    await list_items_for_action(fake_update, context)
    return ConversationHandler.END

def register(app: Application):
    cancel_handlers = [CommandHandler('cancelar', cancel_conv), CallbackQueryHandler(cancel_conv, pattern='^cancel_conv$')]
    edit_header_conv = ConversationHandler(entry_points=[CallbackQueryHandler(start_header_edit, pattern=f"^{CONFIG['prefix']}_edit_header$")], states={AWAITING_HEADER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_modified_header)]}, fallbacks=cancel_handlers)
    add_conv = ConversationHandler(entry_points=[CallbackQueryHandler(add_item_start, pattern=f"^{CONFIG['prefix']}_add_start$")], states={AWAITING_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)], AWAITING_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_item)],}, fallbacks=cancel_handlers)
    modify_conv = ConversationHandler(entry_points=[CallbackQueryHandler(modify_item_start, pattern=f"^{CONFIG['prefix']}_modify_\\d+$")], states={AWAITING_MOD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_modified_title)], AWAITING_MOD_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_modified_item)],}, fallbacks=cancel_handlers)

    app.add_handler(edit_header_conv); app.add_handler(add_conv); app.add_handler(modify_conv)
    app.add_handler(CallbackQueryHandler(prices_hub, pattern='^prices_admin_hub$'))
    app.add_handler(CallbackQueryHandler(list_items_for_action, pattern=f"^{CONFIG['prefix']}_(modify|delete)_list$"))
    app.add_handler(CallbackQueryHandler(confirm_delete_item, pattern=f"^{CONFIG['prefix']}_delete_\\d+$"))
    app.add_handler(CallbackQueryHandler(execute_delete_item, pattern=f"^{CONFIG['prefix']}_delete_execute_confirm_\\d+$"))