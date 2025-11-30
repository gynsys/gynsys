# features/galeria/admin_handlers.py
import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, Chat
from telegram.ext import Application, ConversationHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, CommandHandler
import html

from database import content_db
from common.decorators import superadmin_required, doctor_required
from common.context_manager import get_tenant_id
from common.keyboards import get_delete_confirmation_keyboard # Suponiendo que tienes este archivo
from . import keyboards as admin_keyboards

logger = logging.getLogger(__name__)

CONFIG = {'singular': 'Ítem de Galería', 'plural': 'Galería', 'table': 'gallery', 'title_col': 'title', 'content_col': 'content', 'prefix': 'gallery'}
(AWAITING_TITLE, AWAITING_CONTENT, AWAITING_MEDIA,
 AWAITING_MOD_TITLE, AWAITING_MOD_CONTENT, AWAITING_MOD_MEDIA, AWAITING_HEADER_TEXT) = range(7)


# --- HELPERS ---
def escape_html(text: str) -> str:
    return html.escape(str(text or ''))

# --- CONVERSATION ---
async def cancel_gallery_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    chat_id = update.effective_chat.id

    for key in ['current_photo_message_id', 'main_conv_message_id', 'current_preview_message_id']:
        if msg_id := context.user_data.pop(key, None):
            try: await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception: pass

    if query: await query.answer("Operación cancelada.")
    elif update.message:
        try: await update.message.delete()
        except Exception: pass

    await galeria_hub(update, context, send_new=True)
    context.user_data.clear()
    return ConversationHandler.END

# --- MAIN HUB ---
@superadmin_required
async def galeria_hub(update: Update, context: ContextTypes.DEFAULT_TYPE, send_new: bool = False):
    query = update.callback_query
    message_to_use = query.message if query else update.effective_message
    if query: await query.answer()

    keyboard = [
        [InlineKeyboardButton(f"✏️ Editar Encabezado", callback_data=f"{CONFIG['prefix']}_edit_header")],
        [InlineKeyboardButton(f"➕ Añadir {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_add_start")],
        [InlineKeyboardButton(f"✏️ Modificar {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_modify_list")],
        [InlineKeyboardButton(f"🗑️ Eliminar {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_delete_list")],
       
        # El callback 'open_superadmin_panel' parece ser el correcto según tu main.py
        [InlineKeyboardButton("🔙 Volver a Panel Admin", callback_data='open_superadmin_panel')]
    ]
    text = f"🔧 <b>Gestión de {CONFIG['plural']}</b>"
    reply_markup = InlineKeyboardMarkup(keyboard)

    if send_new or not message_to_use:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup, parse_mode='HTML')
    else:
        try:
            if hasattr(message_to_use, 'edit_text'):
                await message_to_use.edit_text(text, reply_markup=reply_markup, parse_mode='HTML')
            else:
                # Es un objeto fake, usar bot.edit_message_text
                await context.bot.edit_message_text(
                    chat_id=message_to_use.chat.id,
                    message_id=message_to_use.message_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        except Exception:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup, parse_mode='HTML')

# --- LIST & DELETE ---
@superadmin_required
async def list_items_for_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    action = query.data.split('_')[1]
    tenant_id = await get_tenant_id(update, context)
    reply_markup = await admin_keyboards.get_gallery_for_action_keyboard(tenant_id, action)
    if not reply_markup:
        await query.answer(f"No hay ítems para gestionar.", show_alert=True); return
    action_text = 'modificar' if action == 'modify' else 'eliminar'
    await query.message.edit_text(f"Selecciona el ítem que deseas {action_text}:", reply_markup=reply_markup, parse_mode='HTML')


@superadmin_required
async def confirm_delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    item_id = int(query.data.split('_')[-1])
    item_details = await content_db.get_item_details_with_media(
        item_id, CONFIG['table'], CONFIG['title_col'], CONFIG['content_col']
    )

    # VALIDACIÓN MULTI-TENANT
    if not item_details:
        await query.answer("Ítem no encontrado o no pertenece a este bot.", show_alert=True)
        return

    item_name = item_details.get('title', 'este elemento')
    callback = f"{CONFIG['prefix']}_delete_execute_confirm_{item_id}"

    await query.message.edit_text(
        f"<b>⚠️ ¿Seguro que quieres eliminar?</b>\n<blockquote>{escape_html(item_name)}</blockquote>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Sí, eliminar", callback_data=callback)],
            [InlineKeyboardButton("❌ No, cancelar", callback_data=f"{CONFIG['prefix']}_delete_list")]
        ]),
        parse_mode='HTML'
    )

@superadmin_required
async def execute_delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    item_id = int(query.data.split('_')[-1])
    if await content_db.delete_item(item_id, CONFIG['table']):
        await query.answer("✅ Elemento eliminado.", show_alert=True)
    else:
        await query.answer("❌ Error al eliminar.", show_alert=True)
    
    fake_query = type(
        'obj',
        (object,),
        {
            'data': f"{CONFIG['prefix']}_delete_list",
            'message': query.message,
            'answer': query.answer
        }
    )()
    fake_update = type(
        'obj',
        (object,),
        {
            'callback_query': fake_query,
            'effective_user': update.effective_user,
            'effective_chat': update.effective_chat
        }
    )()
    await list_items_for_action(fake_update, context)



# --- ADD ITEM CONVERSATION ---
@superadmin_required
async def add_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    context.user_data['main_conv_message_id'] = query.message.message_id
    await query.message.edit_text(f"✍️ <b>Paso 1/3:</b> Envía el <b>título</b>...\n\n<i>/cancelar para detener.</i>", parse_mode='HTML')
    return AWAITING_TITLE

async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['item_title'] = update.message.text
    await update.message.delete()
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['main_conv_message_id'], text="✅ Título guardado.\n\n📝 <b>Paso 2/3:</b> Ahora, envía la <b>descripción</b> (puedes usar formato <b>HTML</b>).", parse_mode='HTML')
    return AWAITING_CONTENT

async def receive_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['item_content'] = update.message.text_html
    await update.message.delete()
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['main_conv_message_id'], text=f"🖼️ <b>Paso 3/3:</b> Ahora, <b>envía la foto o video</b> para este {CONFIG['singular']}.", parse_mode='HTML')
    return AWAITING_MEDIA

async def save_new_item_with_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    media_file_id, media_type = (message.photo[-1].file_id, 'photo') if message.photo else (message.video.file_id, 'video')
    title = context.user_data.pop('item_title')
    content = context.user_data.pop('item_content')
    tenant_id = await get_tenant_id(update, context)

    try:
        await content_db.add_item_with_media(tenant_id, CONFIG['table'], title, content, media_file_id, media_type, CONFIG['title_col'], CONFIG['content_col'])
        await message.delete()

        main_conv_message_id = context.user_data.pop('main_conv_message_id', None)
        
        if main_conv_message_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=main_conv_message_id,
                    text=f"✅ ¡{CONFIG['singular']} añadido!"
                )
                await asyncio.sleep(1.5)
            except Exception as e:
                logger.warning(f"Error editando mensaje: {e}")
        
        # Objeto completo para galeria_hub
        fake_chat = type('obj', (object,), {'id': update.effective_chat.id, 'type': update.effective_chat.type})()
        fake_message = type('obj', (object,), {
            'message_id': main_conv_message_id,
            'chat': fake_chat,
            'date': update.effective_message.date,
            'from_user': update.effective_user
        })()
        fake_update = type('obj', (object,), {
            'effective_user': update.effective_user,
            'effective_chat': update.effective_chat,
            'effective_message': fake_message,
            'callback_query': None
        })()
        await galeria_hub(fake_update, context, send_new=False)
        
        context.user_data.clear()
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error guardando item de galería: {e}", exc_info=True)
        await message.reply_text("❌ Error al guardar el ítem. Intenta nuevamente.")
        context.user_data.clear()
        return ConversationHandler.END

# --- MODIFY ITEM CONVERSATION ---
@superadmin_required
async def modify_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    item_id = int(query.data.split('_')[-1])
    item_details = await content_db.get_item_details_with_media(item_id, CONFIG['table'], CONFIG['title_col'], CONFIG['content_col'])
    if not item_details:
        await query.answer("El ítem no fue encontrado.", show_alert=True); return ConversationHandler.END

    context.user_data.update({'item_id_to_modify': item_id, 'original_item': item_details, 'main_conv_message_id': query.message.message_id})
    await query.message.edit_text(f"✏️ Modificando '{escape_html(item_details['title'])}'.\n\n<b>Título actual:</b>\n<blockquote>{escape_html(item_details['title'])}</blockquote>\nEnvía el <b>nuevo título</b> o '.' para mantener.\n\n<i>/cancelar para detener.</i>", parse_mode='HTML')
    return AWAITING_MOD_TITLE

async def receive_modified_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != '.': context.user_data['new_title'] = update.message.text
    await update.message.delete()
    original_item = context.user_data['original_item']
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['main_conv_message_id'], text=f"<b>Contenido actual:</b>\n<blockquote>{original_item['content']}</blockquote>\nEnvía el <b>nuevo contenido</b> o '.' para mantener.", parse_mode='HTML')
    return AWAITING_MOD_CONTENT

async def receive_modified_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text_html != '.': context.user_data['new_content'] = update.message.text_html
    await update.message.delete()
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['main_conv_message_id'], text="🖼️ <b>Media actual:</b> (se mostrará abajo)\n\nEnvía una <b>nueva foto o video</b> para reemplazarla, o envía `.` para mantener.", parse_mode='HTML')
    
    original_item = context.user_data.get('original_item', {})
    media_file_id, media_type = original_item.get('media_file_id'), original_item.get('media_type')
    if media_file_id and media_type:
        try:
            sender_func = context.bot.send_photo if media_type == 'photo' else context.bot.send_video
            media_message = await sender_func(chat_id=update.effective_chat.id, **{media_type: media_file_id})
            context.user_data['current_preview_message_id'] = media_message.message_id
        except Exception as e:
            logger.error(f"No se pudo enviar media de preview: {e}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="<i>(No se pudo mostrar el media actual)</i>", parse_mode='HTML')
    return AWAITING_MOD_MEDIA

async def receive_modified_media_or_skip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ud = context.user_data
    if preview_id := ud.pop('current_preview_message_id', None):
        try: await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=preview_id)
        except Exception: pass

    new_media_file_id, new_media_type = (None, None)
    if update.message.photo: new_media_file_id, new_media_type = update.message.photo[-1].file_id, 'photo'
    elif update.message.video: new_media_file_id, new_media_type = update.message.video.file_id, 'video'
    
    await update.message.delete()

    original_item = ud.pop('original_item')
    await content_db.update_item_with_media(
        item_id=ud.pop('item_id_to_modify'), table_name=CONFIG['table'],
        title=ud.get('new_title', original_item['title']),
        content=ud.get('new_content', original_item['content']),
        media_file_id=new_media_file_id or original_item.get('media_file_id'),
        media_type=new_media_type or original_item.get('media_type'),
        title_column=CONFIG['title_col'], content_column=CONFIG['content_col']
    )

    message_to_edit = await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=ud.pop('main_conv_message_id'), text=f"✅ ¡{CONFIG['singular']} actualizado!")
    await asyncio.sleep(2)
    
    fake_query = type('obj', (object,), {'data': f"{CONFIG['prefix']}_modify_list", 'message': message_to_edit, 'answer': lambda *a, **k: asyncio.sleep(0)})()
    await list_items_for_action(type('obj', (object,), {'callback_query': fake_query, 'effective_user': update.effective_user})(), context)

    context.user_data.clear()
    return ConversationHandler.END

# --- HEADER EDIT ---
@superadmin_required
async def start_header_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    tenant_id = await get_tenant_id(update, context); header_key = "header_galeria"
    context.user_data.update({'header_key_to_edit': header_key, 'main_conv_message_id': query.message.message_id})
    current_header = await content_db.get_content(header_key, tenant_id) or "(Sin encabezado definido)"
    await query.message.edit_text(f"✍️ Editando encabezado...\n\n<b>Texto actual:</b>\n<blockquote>{escape_html(current_header)}</blockquote>\n\nEnvía el nuevo texto.\n\n<i>/cancelar para detener.</i>", parse_mode='HTML')
    return AWAITING_HEADER_TEXT

async def save_modified_header(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    new_header = update.message.text_html; await update.message.delete()
    header_key = context.user_data.pop('header_key_to_edit')
    tenant_id = await get_tenant_id(update, context)
    await content_db.update_content(header_key, new_header, tenant_id)

    message_to_edit = await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data.pop('main_conv_message_id'), text="✅ Encabezado actualizado.")
    await asyncio.sleep(2)
    await galeria_hub(type('obj', (object,), {'effective_message': message_to_edit, 'callback_query': None, 'effective_user': update.effective_user})(), context)
    context.user_data.clear()
    return ConversationHandler.END