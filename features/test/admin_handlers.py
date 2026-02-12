# features/test/admin_handlers.py
import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, ConversationHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, CommandHandler

from database import content_db
from common.decorators import doctor_required
from common.helpers import escape_html
from common.keyboards import get_delete_confirmation_keyboard
from common.conversation_utils import cancel_conv
from common.context_manager import get_tenant_id
from database import extra_modules_db
from utils.role_manager import RoleManager
from config import DB_PATH

logger = logging.getLogger(__name__)
role_manager = RoleManager(DB_PATH)

# --- CONFIGURACIÓN ESPECÍFICA DEL MÓDULO ---
CONFIG = {'singular': 'Pregunta del Test', 'plural': 'Preguntas del Test', 'table': 'test_questions', 'title_col': 'question', 'content_col': None, 'prefix': 'testq'}
(AWAITING_NEW_QUESTION, AWAITING_MODIFIED_QUESTION) = range(2)

# --- HUB DE GESTIÓN ---
@doctor_required
async def test_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Verificar que el módulo test esté activo para este doctor
    user_id = update.effective_user.id
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    if not doctor:
        await query.answer("❌ Error: No se encontró el doctor.", show_alert=True)
        return
    
    doctor_id = doctor[0]
    is_active = await extra_modules_db.is_module_active_for_doctor(doctor_id, 'test')
    if not is_active:
        await query.answer("❌ El módulo Test no está activo para tu cuenta.", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton(f"➕ Añadir {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_add_start")],
        [InlineKeyboardButton(f"✏️ Modificar {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_modify_list")],
        [InlineKeyboardButton(f"🗑️ Eliminar {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_delete_list")],
        [InlineKeyboardButton("🔙 Volver", callback_data='doctor_panel')]
    ]
    await query.edit_message_text(
        f"🔧 <b>Gestión de {CONFIG['plural']}</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# --- LÓGICA CRUD ---
@doctor_required
async def list_items_for_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Verificar módulo activo
    user_id = update.effective_user.id
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    if not doctor:
        await query.answer("❌ Error: No se encontró el doctor.", show_alert=True)
        return
    
    doctor_id = doctor[0]
    is_active = await extra_modules_db.is_module_active_for_doctor(doctor_id, 'test')
    if not is_active:
        await query.answer("❌ El módulo Test no está activo.", show_alert=True)
        return
    
    action = query.data.split('_')[1]
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await query.answer("❌ Error al obtener tenant ID.", show_alert=True)
        return
    
    items = await content_db.get_all_items(bot_id, CONFIG['table'], CONFIG['title_col'])
    if not items:
        await query.answer(f"No hay {CONFIG['plural'].lower()} para gestionar.", show_alert=True); return

    edited_ids = context.user_data.get('edited_test_questions', set())
    emoji = "✏️" if action == "modify" else "🗑️"
    keyboard = []
    for item in items:
        edited_indicator = " ✅" if action == "modify" and item['id'] in edited_ids else ""
        title = item['title']
        if len(title) > 40:
            title = title[:37] + "..."
        button_text = f"{emoji} {title}{edited_indicator}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"{CONFIG['prefix']}_{action}_{item['id']}")])

    # --- LÍNEA CORREGIDA ---
    # El callback ahora apunta al hub correcto de este módulo
    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="test_admin_hub")])

    await query.edit_message_text(
        f"Selecciona la {CONFIG['singular'].lower()} que deseas {action}:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

@doctor_required
async def confirm_delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    item_id = int(query.data.split('_')[-1])
    item_details = await content_db.get_item_details(item_id, CONFIG['table'], CONFIG['title_col'], CONFIG['content_col'])
    item_name = item_details.get('title', 'este elemento') if item_details else 'este elemento'
    callback_for_confirmation = f"{CONFIG['prefix']}_delete_execute_confirm_{item_id}"
    await query.edit_message_text(f"<b>⚠️ ¿Seguro que quieres eliminar?</b>\n\n<blockquote>{escape_html(item_name)}</blockquote>",
        reply_markup=get_delete_confirmation_keyboard(item_type_callback=callback_for_confirmation, back_callback=f"{CONFIG['prefix']}_delete_list"))

@doctor_required
async def execute_delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    item_id = int(query.data.split('_')[-1])
    if await content_db.delete_item(item_id, CONFIG['table']):
        await query.answer("✅ Elemento eliminado.", show_alert=True)
    fake_query = type('obj', (object,), {'data': f"{CONFIG['prefix']}_delete_list", 'message': query.message, 'answer': lambda *a, **k: asyncio.sleep(0), 'edit_message_text': query.message.edit_text})()
    fake_update = type('obj', (object,), {'callback_query': fake_query, 'effective_user': update.effective_user})()
    await list_items_for_action(fake_update, context)

@doctor_required

# --- CONVERSATION HANDLER PARA AÑADIR ---
@doctor_required
async def add_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    # Verificar módulo activo
    user_id = update.effective_user.id
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    if not doctor:
        await query.answer("❌ Error: No se encontró el doctor.", show_alert=True)
        return ConversationHandler.END
    
    doctor_id = doctor[0]
    is_active = await extra_modules_db.is_module_active_for_doctor(doctor_id, 'test')
    if not is_active:
        await query.answer("❌ El módulo Test no está activo.", show_alert=True)
        return ConversationHandler.END
    
    context.user_data['main_conv_message_id'] = query.message.message_id
    await query.edit_message_text(
        f"✍️ Envía el <b>texto de la pregunta</b> para el nuevo {CONFIG['singular']}.\n\n<i>/cancelar para detener.</i>",
        parse_mode="HTML"
    )
    return AWAITING_NEW_QUESTION

async def save_new_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    question_text = update.message.text_html
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await update.message.reply_text("❌ Error: No se pudo obtener el tenant ID.")
        return ConversationHandler.END
    
    await content_db.add_item(bot_id, CONFIG['table'], question_text, None, CONFIG['title_col'], None)
    await update.message.delete()
    message_to_edit = await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data.pop('main_conv_message_id'), text=f"✅ ¡{CONFIG['singular']} añadida con éxito!")
    await asyncio.sleep(2)
    fake_query = type('obj', (object,), {'message': message_to_edit, 'answer': lambda *a, **k: asyncio.sleep(0), 'edit_message_text': message_to_edit.edit_text})()
    fake_update = type('obj', (object,), {'callback_query': fake_query, 'effective_user': update.effective_user})()
    await test_hub(fake_update, context)
    return ConversationHandler.END

# --- CONVERSATION HANDLER PARA MODIFICAR ---
@doctor_required
async def modify_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    # Verificar módulo activo
    user_id = update.effective_user.id
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    if not doctor:
        await query.answer("❌ Error: No se encontró el doctor.", show_alert=True)
        return ConversationHandler.END
    
    doctor_id = doctor[0]
    is_active = await extra_modules_db.is_module_active_for_doctor(doctor_id, 'test')
    if not is_active:
        await query.answer("❌ El módulo Test no está activo.", show_alert=True)
        return ConversationHandler.END
    
    item_id = int(query.data.split('_')[-1])
    item_details = await content_db.get_item_details(item_id, CONFIG['table'], CONFIG['title_col'], None)
    if not item_details:
        return ConversationHandler.END
    
    context.user_data.update({'item_id_to_modify': item_id, 'original_item': item_details, 'main_conv_message_id': query.message.message_id})
    await query.edit_message_text(
        f"✏️ Modificando pregunta:\n\n<b>Texto actual:</b>\n<blockquote>{escape_html(item_details['title'])}</blockquote>\nEnvía el <b>nuevo texto</b> para la pregunta.\n\n<i>/cancelar para detener.</i>",
        parse_mode="HTML"
    )
    return AWAITING_MODIFIED_QUESTION

async def save_modified_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_text = update.message.text_html
    await update.message.delete()
    ud = context.user_data
    item_id = ud.pop('item_id_to_modify')
    await content_db.update_item(item_id, CONFIG['table'], new_text, None, CONFIG['title_col'], None)

    if 'edited_test_questions' not in context.user_data: context.user_data['edited_test_questions'] = set()
    context.user_data['edited_test_questions'].add(item_id)

    message_to_edit = await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=ud.pop('main_conv_message_id'), text=f"✅ ¡{CONFIG['singular']} actualizada con éxito!")
    await asyncio.sleep(2)
    fake_query = type('obj', (object,), {'data': f"{CONFIG['prefix']}_modify_list", 'message': message_to_edit, 'answer': lambda *a, **k: asyncio.sleep(0), 'edit_message_text': message_to_edit.edit_text})()
    fake_update = type('obj', (object,), {'callback_query': fake_query, 'effective_user': update.effective_user})()
    await list_items_for_action(fake_update, context)
    return ConversationHandler.END

# --- REGISTRO DE HANDLERS ---
def register(app: Application):
    cancel_handlers = [CommandHandler('cancelar', cancel_conv), CallbackQueryHandler(cancel_conv, pattern='^cancel_conv$')]
    add_conv = ConversationHandler(entry_points=[CallbackQueryHandler(add_item_start, pattern=f"^{CONFIG['prefix']}_add_start$")], states={AWAITING_NEW_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_question)]}, fallbacks=cancel_handlers)
    modify_conv = ConversationHandler(entry_points=[CallbackQueryHandler(modify_item_start, pattern=f"^{CONFIG['prefix']}_modify_\\d+$")], states={AWAITING_MODIFIED_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_modified_question)]}, fallbacks=cancel_handlers)

    app.add_handler(add_conv)
    app.add_handler(modify_conv)
    app.add_handler(CallbackQueryHandler(test_hub, pattern='^test_admin_hub$'))
    app.add_handler(CallbackQueryHandler(list_items_for_action, pattern=f"^{CONFIG['prefix']}_(modify|delete)_list$"))
    app.add_handler(CallbackQueryHandler(confirm_delete_item, pattern=f"^{CONFIG['prefix']}_delete_\\d+$"))
    app.add_handler(CallbackQueryHandler(execute_delete_item, pattern=f"^{CONFIG['prefix']}_delete_execute_confirm_\\d+$"))