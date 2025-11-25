# features/ubicaciones/admin_handlers.py
import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, ConversationHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, CommandHandler

from database import locations_db, content_db
from common.decorators import admin_required
from common.helpers import escape_html
from common.keyboards import get_delete_confirmation_keyboard
from common.conversation_utils import cancel_conv
from common.context_manager import get_tenant_id

from . import keyboards as admin_keyboards # Importamos los teclados locales

logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN Y ESTADOS ---
CONFIG = {'singular': 'Ubicación', 'plural': 'Ubicaciones', 'table': 'locations', 'prefix': 'loc'}
(AWAITING_NAME, AWAITING_ADDRESS, AWAITING_SCHEDULE, AWAITING_GMAPS,
 AWAITING_MOD_NAME, AWAITING_MOD_ADDRESS, AWAITING_MOD_SCHEDULE, AWAITING_MOD_GMAPS,
 AWAITING_HEADER_TEXT) = range(9)

# --- HUB DE GESTIÓN ---
@admin_required
async def locations_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()

    # --- TECLADO CORREGIDO Y COMPLETO ---
    keyboard = [
        # --- ¡BOTÓN AÑADIDO! ---
        # [InlineKeyboardButton(f"✏️ Editar Encabezado", callback_data=f"{CONFIG['prefix']}_edit_header")],



        [InlineKeyboardButton(f"➕ Añadir {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_add_start")],
        [InlineKeyboardButton(f"✏️ Modificar {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_modify_list")],
        [InlineKeyboardButton(f"🗑️ Eliminar {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_delete_list")],
        [
            InlineKeyboardButton("🔙 Volver", callback_data='doctor_panel'),
            InlineKeyboardButton("🏠 Menú Principal", callback_data='main_menu')
        ]
    ]

    await query.edit_message_text(f"🔧 <b>Gestión de {CONFIG['plural']}</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")

# --- NUEVA CONVERSATION HANDLER PARA EDITAR HEADER ---
@admin_required
async def start_header_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    bot_id = await get_tenant_id(update, context)
    header_key = f"header_sedes" # Clave específica para el header de ubicaciones

    context.user_data['header_key_to_edit'] = header_key
    context.user_data['main_conv_message_id'] = query.message.message_id

    current_header = await content_db.get_content(header_key, bot_id) or "(Sin encabezado definido)"

    await query.edit_message_text(
        f"✍️ Editando encabezado para <b>{CONFIG['plural']}</b>\n\n"
        f"<b>Texto actual:</b>\n<blockquote>{current_header}</blockquote>\n\n"
        "Envía el nuevo texto del encabezado.\n\n<i>/cancelar para detener.</i>",
        parse_mode="HTML"
    )
    return AWAITING_HEADER_TEXT

async def save_modified_header(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_header = update.message.text_html
    await update.message.delete()

    header_key = context.user_data.pop('header_key_to_edit')
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await update.message.reply_text("❌ No se pudo determinar el perfil del médico.")
        return ConversationHandler.END
    await content_db.update_content(header_key, new_header, bot_id)

    message_to_edit = await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data.pop('main_conv_message_id'),
        text="✅ Encabezado actualizado."
    )
    await asyncio.sleep(2)

    # --- FAKE UPDATE CORREGIDO ---
    # Añadimos el método 'edit_message_text' a nuestro objeto simulado
    fake_query = type('obj', (object,), {
        'data': 'locations_admin_hub',
        'message': message_to_edit,
        'answer': lambda *a, **k: asyncio.sleep(0),
        'edit_message_text': message_to_edit.edit_text # <-- ¡LA PIEZA QUE FALTABA!
    })()
    fake_update = type('obj', (object,), {
        'callback_query': fake_query,
        'effective_user': update.effective_user
    })()

    await locations_hub(fake_update, context)
    return ConversationHandler.END
# --- LÓGICA DE LISTADO, ELIMINACIÓN Y REORDENACIÓN ---
@admin_required
async def list_items_for_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    action = query.data.split('_')[1]
    bot_id = await get_tenant_id(update, context)
    reply_markup = await admin_keyboards.get_locations_for_action_keyboard(bot_id, action)
    if not reply_markup:
        await query.answer(f"No hay {CONFIG['plural'].lower()} para gestionar.", show_alert=True); return
    action_text = 'modificar' if action == 'modify' else 'eliminar'
    await query.edit_message_text(f"Selecciona la {CONFIG['singular'].lower()} que deseas {action_text}:", reply_markup=reply_markup)

@admin_required
async def confirm_delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    item_id = int(query.data.split('_')[-1])

    # --- ¡LLAMADA CORREGIDA! ---
    # Usamos el módulo 'locations_db'
    loc = await locations_db.get_location_details(item_id)

    item_name = loc['name'] if loc else 'esta ubicación'
    callback_for_confirmation = f"{CONFIG['prefix']}_delete_execute_confirm_{item_id}"
    await query.edit_message_text(f"<b>⚠️ ¿Seguro que quieres eliminar?</b>\n\n<blockquote>{escape_html(item_name)}</blockquote>",
        reply_markup=get_delete_confirmation_keyboard(item_type_callback=callback_for_confirmation, back_callback=f"{CONFIG['prefix']}_delete_list"), parse_mode="HTML")

# --- FUNCIÓN CORREGIDA ---
@admin_required
async def execute_delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    item_id = int(query.data.split('_')[-1])

    # --- ¡LLAMADA CORREGIDA! ---
    # Usamos el módulo 'locations_db'
    if await locations_db.delete_location(item_id):
        await query.answer("✅ Ubicación eliminada.", show_alert=True)

    # El fake_update está bien, pero asegurémonos de que la llamada sea a list_items_for_action
    fake_query = type('obj', (object,), {
        'data': f"{CONFIG['prefix']}_delete_list",
        'message': query.message,
        'answer': lambda *a, **k: asyncio.sleep(0),
        'edit_message_text': query.message.edit_text
    })()
    fake_update = type('obj', (object,), {
        'callback_query': fake_query,
        'effective_user': update.effective_user
    })()

    await list_items_for_action(fake_update, context)

@admin_required
# --- CONVERSATION HANDLER PARA AÑADIR UBICACIÓN ---
@admin_required
async def add_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    context.user_data['main_conv_message_id'] = query.message.message_id
    await query.edit_message_text(f"✍️ Envía el <b>nombre</b> para la nueva {CONFIG['singular']}.\n\n<i>/cancelar para detener.</i>", parse_mode="HTML")
    return AWAITING_NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['loc_name'] = update.message.text
    await update.message.delete()
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['main_conv_message_id'], text="✅ Nombre guardado. Ahora, envía la <b>dirección completa</b>.", parse_mode="HTML")
    return AWAITING_ADDRESS

async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['loc_address'] = update.message.text
    await update.message.delete()
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['main_conv_message_id'], text="OK. Ahora envía el <b>horario</b> (ej: Lunes a Viernes 9am-5pm).", parse_mode="HTML")
    return AWAITING_SCHEDULE

async def receive_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['loc_schedule'] = update.message.text
    await update.message.delete()
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['main_conv_message_id'], text="Finalmente, envía el <b>enlace de Google Maps</b>.", parse_mode="HTML")
    return AWAITING_GMAPS

async def save_new_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ud = context.user_data
    gmaps_url = update.message.text
    bot_id = await get_tenant_id(update, context)
    
    if not bot_id:
        await update.message.reply_text("❌ No se pudo determinar el perfil del médico.")
        return ConversationHandler.END

    # --- ¡LLAMADA CORREGIDA! ---
    # Ahora usamos el módulo 'locations_db'
    await locations_db.add_location(bot_id, ud['loc_name'], ud['loc_address'], ud['loc_schedule'], gmaps_url)

    await update.message.delete()
    message_to_edit = await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=ud.pop('main_conv_message_id'),
        text=f"✅ ¡{CONFIG['singular']} añadida con éxito!"
    )
    await asyncio.sleep(2)

    fake_query = type('obj', (object,), {
        'message': message_to_edit,
        'answer': lambda *a, **k: asyncio.sleep(0),
        'edit_message_text': message_to_edit.edit_text
    })()
    fake_update = type('obj', (object,), {
        'callback_query': fake_query,
        'effective_user': update.effective_user
    })()

    await locations_hub(fake_update, context)
    return ConversationHandler.END

# --- CONVERSATION HANDLER PARA MODIFICAR UBICACIÓN ---
@admin_required
async def modify_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    item_id = int(query.data.split('_')[-1])

    # --- ¡LLAMADA CORREGIDA! ---
    loc = await locations_db.get_location_details(item_id)

    if not loc:
        await query.answer("❌ Ubicación no encontrada.", show_alert=True)
        return ConversationHandler.END

    context.user_data.update({'item_id_to_modify': item_id, 'original_loc': loc, 'main_conv_message_id': query.message.message_id})
    await query.edit_message_text(f"✏️ Modificando '{loc['name']}'.\n\n<b>Nombre actual:</b>\n<blockquote>{escape_html(loc['name'])}</blockquote>\nEnvía el <b>nuevo nombre</b> o '.' para mantener.\n\n<i>/cancelar para detener.</i>", parse_mode="HTML")
    return AWAITING_MOD_NAME

async def receive_modified_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != '.': context.user_data['new_name'] = update.message.text
    await update.message.delete()
    loc = context.user_data['original_loc']
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['main_conv_message_id'], text=f"<b>Dirección actual:</b>\n<blockquote>{escape_html(loc['address'])}</blockquote>\nEnvía la <b>nueva dirección</b> o '.' para mantener.", parse_mode="HTML")
    return AWAITING_MOD_ADDRESS

async def receive_modified_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != '.': context.user_data['new_address'] = update.message.text
    await update.message.delete()
    loc = context.user_data['original_loc']
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['main_conv_message_id'], text=f"<b>Horario actual:</b>\n<blockquote>{escape_html(loc['schedule'])}</blockquote>\nEnvía el <b>nuevo horario</b> o '.' para mantener.", parse_mode="HTML")
    return AWAITING_MOD_SCHEDULE

async def receive_modified_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != '.': context.user_data['new_schedule'] = update.message.text
    await update.message.delete()
    loc = context.user_data['original_loc']
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['main_conv_message_id'], text=f"<b>Enlace de Maps actual:</b>\n<blockquote>{escape_html(loc['Maps_url'])}</blockquote>\nEnvía el <b>nuevo enlace</b> o '.' para mantener.", parse_mode="HTML")
    return AWAITING_MOD_GMAPS

async def save_modified_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != '.':
        context.user_data['new_gmaps_url'] = update.message.text
    await update.message.delete()

    ud = context.user_data
    original_loc = ud.pop('original_loc')
    item_id = ud.pop('item_id_to_modify')

    final_name = ud.get('new_name', original_loc['name'])
    final_address = ud.get('new_address', original_loc['address'])
    final_schedule = ud.get('new_schedule', original_loc['schedule'])
    final_gmaps_url = ud.get('new_gmaps_url', original_loc['Maps_url'])

    # --- ¡LLAMADA CORREGIDA! ---
    # Ahora usamos el módulo 'locations_db'
    await locations_db.update_location(item_id, final_name, final_address, final_schedule, final_gmaps_url)

    message_to_edit = await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=ud.pop('main_conv_message_id'),
        text=f"✅ ¡{CONFIG['singular']} actualizada con éxito!"
    )
    await asyncio.sleep(2)

    fake_query = type('obj', (object,), {
        'data': f"{CONFIG['prefix']}_modify_list",
        'message': message_to_edit,
        'answer': lambda *a, **k: asyncio.sleep(0),
        'edit_message_text': message_to_edit.edit_text
    })()
    fake_update = type('obj', (object,), {
        'callback_query': fake_query,
        'effective_user': update.effective_user
    })()

    await list_items_for_action(fake_update, context)
    return ConversationHandler.END

def register(app: Application):
    cancel_handlers = [CommandHandler('cancelar', cancel_conv), CallbackQueryHandler(cancel_conv, pattern='^cancel_conv$')]

    # Definimos todas las ConversationHandlers
    edit_header_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_header_edit, pattern=f"^{CONFIG['prefix']}_edit_header$")],
        states={AWAITING_HEADER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_modified_header)]},
        fallbacks=cancel_handlers
    )

    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_item_start, pattern=f"^{CONFIG['prefix']}_add_start$")],
        states={
            AWAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            AWAITING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_address)],
            AWAITING_SCHEDULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_schedule)],
            AWAITING_GMAPS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_location)],
        }, fallbacks=cancel_handlers
    )

    modify_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(modify_item_start, pattern=f"^{CONFIG['prefix']}_modify_\\d+$")],
        states={
            AWAITING_MOD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_modified_name)],
            AWAITING_MOD_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_modified_address)],
            AWAITING_MOD_SCHEDULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_modified_schedule)],
            AWAITING_MOD_GMAPS: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_modified_location)],
        }, fallbacks=cancel_handlers
    )

    # Añadimos todas las ConversationHandlers a la aplicación
    app.add_handler(edit_header_conv)
    app.add_handler(add_conv)
    app.add_handler(modify_conv)

    # Añadimos los CallbackQueryHandlers para navegación y acciones
    app.add_handler(CallbackQueryHandler(locations_hub, pattern='^locations_admin_hub$')) # <-- ¡HANDLER QUE FALTABA!
    app.add_handler(CallbackQueryHandler(list_items_for_action, pattern=f"^{CONFIG['prefix']}_(modify|delete)_list$"))
    app.add_handler(CallbackQueryHandler(confirm_delete_item, pattern=f"^{CONFIG['prefix']}_delete_\\d+$"))
    app.add_handler(CallbackQueryHandler(execute_delete_item, pattern=f"^{CONFIG['prefix']}_delete_execute_confirm_\\d+$"))