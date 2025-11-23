# features/faqs/admin_handlers.py
import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message, User, Chat
from telegram.ext import Application, ConversationHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, CommandHandler

from database import content_db
from common.decorators import admin_required
from common.helpers import escape_html
from common.keyboards import get_delete_confirmation_keyboard
from common.conversation_utils import cancel_conv
from common.context_manager import get_tenant_id
from . import keyboards as admin_keyboards
from .faq_service import add_faq_direct, update_faq_direct, get_faq_details_direct

logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN Y ESTADOS ---
CONFIG = {'singular': 'FAQ', 'plural': 'FAQs', 'table': 'faqs', 'title_col': 'question', 'content_col': 'answer', 'prefix': 'faq'}
(AWAITING_TITLE, AWAITING_CONTENT, AWAITING_MOD_TITLE, AWAITING_MOD_CONTENT, AWAITING_HEADER_TEXT) = range(5)
# --- HUB DE GESTIÓN ---
@admin_required
async def faqs_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📋 [faqs_hub] ========== INICIO ==========")
    print(f"📋 [faqs_hub] Función llamada. User ID: {update.effective_user.id}")
    logger.info(f"[faqs_hub] ========== INICIO ==========")
    logger.info(f"[faqs_hub] Función llamada. User ID: {update.effective_user.id}")
    
    # Verificar si pasó el decorador
    from config import SUPER_ADMIN_ID
    if update.effective_user.id == SUPER_ADMIN_ID:
        print(f"📋 [faqs_hub] ✅ Usuario es SUPER_ADMIN_ID")
        logger.info(f"[faqs_hub] ✅ Usuario es SUPER_ADMIN_ID")
    else:
        print(f"📋 [faqs_hub] Usuario NO es superadmin")
        logger.info(f"[faqs_hub] Usuario NO es superadmin")
    
    query = update.callback_query
    if query:
        # Verificar si query tiene el atributo 'data' (puede ser un objeto simulado)
        if hasattr(query, 'data'):
            logger.info(f"[faqs_hub] Callback query detectado. Data: {query.data}")
        else:
            logger.info(f"[faqs_hub] Callback query detectado (objeto simulado sin data)")
        
        # Intentar answer() solo si es un query real
        if hasattr(query, 'answer'):
            try:
                await query.answer()
                logger.info(f"[faqs_hub] query.answer() ejecutado correctamente")
            except Exception as e:
                logger.error(f"[faqs_hub] Error en query.answer(): {e}")
    else:
        logger.warning(f"[faqs_hub] No hay callback_query en el update")
    
    try:
        bot_id = await get_tenant_id(update, context)
        logger.info(f"[faqs_hub] bot_id obtenido: {bot_id}")
    except Exception as e:
        logger.error(f"[faqs_hub] Error obteniendo bot_id: {e}")
        bot_id = None
    
    keyboard = [
        [InlineKeyboardButton(f"✏️ Editar Encabezado", callback_data=f"{CONFIG['prefix']}_edit_header")],

        [InlineKeyboardButton(f"➕ Añadir {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_add_start")],
        [InlineKeyboardButton(f"✏️ Modificar {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_modify_list")],
        [InlineKeyboardButton(f"🗑️ Eliminar {CONFIG['singular']}", callback_data=f"{CONFIG['prefix']}_delete_list")],
        [InlineKeyboardButton(f"🔄 Reordenar {CONFIG['plural']}", callback_data=f"{CONFIG['prefix']}_reorder_list")],
        [InlineKeyboardButton("🔙 Volver", callback_data='doctor_panel'), InlineKeyboardButton("🏠 Menú Principal", callback_data='main_menu')]
    ]
    
    # Intentar editar mensaje si hay query y tiene método edit_message_text
    if query and hasattr(query, 'edit_message_text') and hasattr(query, 'message'):
        try:
            logger.info(f"[faqs_hub] Intentando editar mensaje...")
            await query.edit_message_text(f"🔧 <b>Gestión de {CONFIG['plural']}</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
            logger.info(f"[faqs_hub] ✅ Mensaje editado exitosamente")
        except Exception as e:
            logger.error(f"[faqs_hub] ❌ Error editando mensaje: {e}", exc_info=True)
            # Intentar enviar nuevo mensaje
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"🔧 <b>Gestión de {CONFIG['plural']}</b>",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="HTML"
                )
                logger.info(f"[faqs_hub] ✅ Mensaje enviado como nuevo mensaje")
            except Exception as e2:
                logger.error(f"[faqs_hub] ❌ Error enviando nuevo mensaje: {e2}", exc_info=True)
    else:
        # Si no hay query válido, enviar nuevo mensaje directamente
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🔧 <b>Gestión de {CONFIG['plural']}</b>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
            logger.info(f"[faqs_hub] ✅ Mensaje enviado (sin query válido)")
        except Exception as e:
            logger.error(f"[faqs_hub] ❌ Error enviando mensaje: {e}", exc_info=True)
    
    logger.info(f"[faqs_hub] ========== FIN ==========")

@admin_required
async def start_header_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    bot_id = await get_tenant_id(update, context)
    header_key = "header_faq" # Clave específica para el header de FAQs

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

    message_to_edit = await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data.pop('main_conv_message_id'), text="✅ Encabezado actualizado.")
    await asyncio.sleep(2)

    fake_query = type('obj', (object,), {'data': 'faqs_admin_hub', 'message': message_to_edit, 'answer': lambda *a, **k: asyncio.sleep(0), 'edit_message_text': message_to_edit.edit_text})()
    fake_update = type('obj', (object,), {'callback_query': fake_query, 'effective_user': update.effective_user})()
    await faqs_hub(fake_update, context)
    return ConversationHandler.END
# --- LÓGICA DE LISTADO, ELIMINACIÓN Y REORDENACIÓN ---
@admin_required
async def list_items_for_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    action = query.data.split('_')[1]
    bot_id = await get_tenant_id(update, context)
    reply_markup = await admin_keyboards.get_faqs_for_action_keyboard(bot_id, action)
    if not reply_markup:
        await query.answer(f"No hay {CONFIG['plural'].lower()} para gestionar.", show_alert=True); return
    action_text = 'modificar' if action == 'modify' else 'eliminar'
    await query.edit_message_text(f"Selecciona la {CONFIG['singular'].lower()} que deseas {action_text}:", reply_markup=reply_markup)

@admin_required
async def confirm_delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    item_id = int(query.data.split('_')[-1])
    item_details = await content_db.get_item_details(item_id, CONFIG['table'], CONFIG['title_col'], CONFIG['content_col'])
    item_name = item_details.get('title', 'este elemento') if item_details else 'este elemento'
    callback_for_confirmation = f"{CONFIG['prefix']}_delete_execute_confirm_{item_id}"
    await query.edit_message_text(f"<b>⚠️ ¿Seguro que quieres eliminar?</b>\n\n<blockquote>{escape_html(item_name)}</blockquote>",
        reply_markup=get_delete_confirmation_keyboard(item_type_callback=callback_for_confirmation, back_callback=f"{CONFIG['prefix']}_delete_list"), parse_mode="HTML")

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
async def list_items_for_reorder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    bot_id = await get_tenant_id(update, context)
    reply_markup = await admin_keyboards.get_faqs_reorder_keyboard(bot_id)
    if not reply_markup:
        await query.answer("No hay suficientes elementos para reordenar.", show_alert=True); return
    await query.edit_message_text(f"🔄 <b>Reordenar {CONFIG['plural']}</b>", reply_markup=reply_markup, parse_mode="HTML")

@admin_required
async def execute_reorder_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(cache_time=1)
    _, _, direction, item_id_str = query.data.split('_')
    item_id = int(item_id_str)
    bot_id = await get_tenant_id(update, context)
    if await content_db.reorder_item(bot_id, CONFIG['table'], item_id, direction):
        fake_query = type('obj', (object,), {'data': f"{CONFIG['prefix']}_reorder_list", 'message': query.message, 'answer': lambda *a, **k: asyncio.sleep(0), 'edit_message_text': query.message.edit_text, 'edit_message_reply_markup': query.message.edit_reply_markup})()
        fake_update = type('obj', (object,), {'callback_query': fake_query, 'effective_user': update.effective_user, 'effective_chat': query.message.chat})()
        await list_items_for_reorder(fake_update, context)
    else:
        await query.answer("❌ No se pudo mover.", show_alert=True)

# --- CONVERSATION HANDLERS (Añadir y Modificar) ---
@admin_required
async def add_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    context.user_data['main_conv_message_id'] = query.message.message_id
    await query.edit_message_text(f"✍️ Envía la <b>pregunta</b> para la nueva {CONFIG['singular']}.\n\n<i>/cancelar para detener.</i>", parse_mode="HTML")
    return AWAITING_TITLE

async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['item_title'] = update.message.text
    await update.message.delete()
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['main_conv_message_id'], text="✅ Pregunta guardada. Ahora, envía la <b>respuesta</b>.", parse_mode="HTML")
    return AWAITING_CONTENT

async def save_new_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Añade una nueva FAQ usando función específica para evitar conflictos"""
    question = context.user_data.pop('item_title', None)
    answer = update.message.text_html if hasattr(update.message, 'text_html') else update.message.text
    
    if not question:
        await update.message.reply_text("❌ Error: No se encontró la pregunta.")
        return ConversationHandler.END
    
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await update.message.reply_text("❌ No se pudo determinar el perfil del médico.")
        return ConversationHandler.END
    
    try:
        # Usar función específica para FAQs
        faq_id = await add_faq_direct(bot_id, question, answer)
        
        if not faq_id:
            await update.message.reply_text(f"❌ Error al guardar la {CONFIG['singular'].lower()}. Por favor, intenta nuevamente.")
            return ConversationHandler.END
        
        await update.message.delete()
        message_to_edit = await context.bot.edit_message_text(
            chat_id=update.effective_chat.id, 
            message_id=context.user_data.pop('main_conv_message_id', None), 
            text=f"✅ ¡{CONFIG['singular']} añadida con éxito!"
        )
        await asyncio.sleep(2)
        
        # Mostrar la lista de FAQs actualizada
        reply_markup = await admin_keyboards.get_faqs_for_action_keyboard(bot_id, "modify")
        
        if reply_markup:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=message_to_edit.message_id,
                    text=f"✅ ¡{CONFIG['singular']} añadida con éxito!\n\n📋 <b>Selecciona la {CONFIG['singular'].lower()} que deseas modificar:</b>",
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error mostrando lista de FAQs: {e}", exc_info=True)
                # Si falla, volver al hub
                fake_query = CallbackQuery(
                    id="fake_query_id",
                    from_user=update.effective_user,
                    chat_instance="fake_chat_instance",
                    data=f"{CONFIG['prefix']}_admin_hub",
                    message=message_to_edit
                )
                fake_update = Update(
                    update_id=0,
                    effective_user=update.effective_user,
                    effective_chat=update.effective_chat,
                    effective_message=message_to_edit,
                    callback_query=fake_query
                )
                await faqs_hub(fake_update, context)
        else:
            # Si no hay FAQs, volver al hub
            fake_query = CallbackQuery(
                id="fake_query_id",
                from_user=update.effective_user,
                chat_instance="fake_chat_instance",
                data=f"{CONFIG['prefix']}_admin_hub",
                message=message_to_edit
            )
            fake_update = Update(
                update_id=0,
                effective_user=update.effective_user,
                effective_chat=update.effective_chat,
                effective_message=message_to_edit,
                callback_query=fake_query
            )
            await faqs_hub(fake_update, context)
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"❌ Error en save_new_item: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error al guardar la {CONFIG['singular'].lower()}. Por favor, intenta nuevamente.")
        return ConversationHandler.END

@admin_required
async def modify_item_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia la modificación de una FAQ usando función específica"""
    query = update.callback_query
    await query.answer()
    
    item_id = int(query.data.split('_')[-1])
    bot_id = await get_tenant_id(update, context)
    
    if not bot_id:
        await query.edit_message_text("❌ No se pudo determinar el perfil del médico.")
        return ConversationHandler.END
    
    # Usar función específica para FAQs
    item_details = await get_faq_details_direct(item_id, bot_id)
    
    if not item_details:
        await query.edit_message_text("❌ FAQ no encontrada.")
        return ConversationHandler.END
    
    context.user_data.update({
        'item_id_to_modify': item_id,
        'original_item': item_details,
        'main_conv_message_id': query.message.message_id,
        'bot_id': bot_id  # Guardar bot_id para validación
    })
    
    await query.edit_message_text(
        f"✏️ Modificando '{escape_html(item_details['title'])}'.\n\n"
        f"<b>Pregunta actual:</b>\n<blockquote>{escape_html(item_details['title'])}</blockquote>\n"
        f"Envía la <b>nueva pregunta</b> o '.' para mantener.\n\n"
        f"<i>/cancelar para detener.</i>",
        parse_mode="HTML"
    )
    return AWAITING_MOD_TITLE

async def receive_modified_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text != '.': context.user_data['new_title'] = update.message.text
    await update.message.delete()
    original_item = context.user_data['original_item']
    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=context.user_data['main_conv_message_id'],
        text=f"<b>Respuesta actual:</b>\n<blockquote>{original_item['content']}</blockquote>\nEnvía la <b>nueva respuesta</b> o '.' para mantener.", parse_mode="HTML")
    return AWAITING_MOD_CONTENT

async def save_modified_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guarda los cambios de una FAQ usando función específica"""
    ud = context.user_data
    
    # Obtener datos del contexto
    original_item = ud.get('original_item')
    item_id = ud.get('item_id_to_modify')
    bot_id = ud.get('bot_id')
    
    if not original_item or not item_id or not bot_id:
        await update.message.reply_text("❌ Error: Datos de modificación no encontrados.")
        return ConversationHandler.END
    
    # Obtener nuevos valores
    new_question = ud.get('new_title')
    new_answer = update.message.text_html if hasattr(update.message, 'text_html') and update.message.text_html != '.' else None
    
    if update.message.text_html == '.':
        new_answer = None
    
    # Si no se proporcionó nuevo valor, mantener el original
    final_question = new_question if new_question else original_item['title']
    final_answer = new_answer if new_answer else original_item['content']
    
    try:
        # Usar función específica para FAQs
        success = await update_faq_direct(item_id, bot_id, final_question, final_answer)
        
        if not success:
            await update.message.reply_text(f"❌ Error al actualizar la {CONFIG['singular'].lower()}.")
            return ConversationHandler.END
        
        await update.message.delete()
        message_to_edit = await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=ud.pop('main_conv_message_id', None),
            text=f"✅ ¡{CONFIG['singular']} actualizado con éxito!"
        )
        await asyncio.sleep(2)
        
        # Limpiar user_data
        ud.pop('item_id_to_modify', None)
        ud.pop('original_item', None)
        ud.pop('new_title', None)
        ud.pop('new_content', None)
        ud.pop('bot_id', None)
        
        # Redirigir a la lista de modificación
        fake_query = CallbackQuery(
            id="fake_query_id",
            from_user=update.effective_user,
            chat_instance="fake_chat_instance",
            data=f"{CONFIG['prefix']}_modify_list",
            message=message_to_edit
        )
        fake_update = Update(
            update_id=0,
            effective_user=update.effective_user,
            effective_chat=update.effective_chat,
            effective_message=message_to_edit,
            callback_query=fake_query
        )
        await list_items_for_action(fake_update, context)
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"❌ Error en save_modified_item: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error al actualizar la {CONFIG['singular'].lower()}.")
        return ConversationHandler.END

def register(app: Application):
    cancel_handlers = [CommandHandler('cancelar', cancel_conv), CallbackQueryHandler(cancel_conv, pattern='^cancel_conv$')]
    # Aquí iría la ConversationHandler para editar el header

    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_item_start, pattern=f"^{CONFIG['prefix']}_add_start$")], 
        states={
            AWAITING_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)], 
            AWAITING_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_item)]
        }, 
        fallbacks=cancel_handlers,
        allow_reentry=True  # Permite añadir múltiples FAQs seguidas
    )
    modify_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(modify_item_start, pattern=f"^{CONFIG['prefix']}_modify_\\d+$")], 
        states={
            AWAITING_MOD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_modified_title)], 
            AWAITING_MOD_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_modified_item)]
        }, 
        fallbacks=cancel_handlers,
        allow_reentry=True  # Permite modificar múltiples FAQs seguidas
    )
    edit_header_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_header_edit, pattern=f"^{CONFIG['prefix']}_edit_header$")],
        states={AWAITING_HEADER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_modified_header)]},
        fallbacks=cancel_handlers,
        allow_reentry=True  # Permite editar el header múltiples veces
    )

    app.add_handler(add_conv); app.add_handler(modify_conv)
    app.add_handler(CallbackQueryHandler(faqs_hub, pattern='^faqs_admin_hub$'))
    app.add_handler(edit_header_conv)
    app.add_handler(CallbackQueryHandler(list_items_for_action, pattern=f"^{CONFIG['prefix']}_(modify|delete)_list$"))
    app.add_handler(CallbackQueryHandler(confirm_delete_item, pattern=f"^{CONFIG['prefix']}_delete_\\d+$"))
    app.add_handler(CallbackQueryHandler(execute_delete_item, pattern=f"^{CONFIG['prefix']}_delete_execute_confirm_\\d+$"))
    app.add_handler(CallbackQueryHandler(list_items_for_reorder, pattern=f"^{CONFIG['prefix']}_reorder_list$"))
    app.add_handler(CallbackQueryHandler(execute_reorder_item, pattern=f"^{CONFIG['prefix']}_reorder_(up|down)_\\d+$"))