# /features/faqs/user_handlers.py
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters
)
from telegram.error import BadRequest
from database import content_db, user_db
from common.helpers import escape_html
from common import texts, helpers
from common.context_manager import get_tenant_id
from .keyboards import get_faq_keyboard
from common.keyboards import get_back_to_menu_keyboard, get_return_to_main_menu_keyboard
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)
(AWAITING_QUESTION,) = range(1)

async def show_faqs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra directamente la primera pregunta con navegación por flechas"""
    query = update.callback_query
    await query.answer()
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        bot_id = 1  # Fallback a SuperAdmin
    
    # Obtener todas las FAQs
    items = await content_db.get_all_items(bot_id, 'faqs', 'question')
    
    if not items:
        # Si no hay FAQs, mostrar mensaje
        texto = "❓ <b>Preguntas Frecuentes</b>\n\nNo hay preguntas frecuentes disponibles en este momento."
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Menú Principal", callback_data='main_menu')]
        ])
    else:
        # Guardar las FAQs en user_data para navegación
        context.user_data['faqs_list'] = items
        context.user_data['faq_current_index'] = 0
        
        # Mostrar la primera pregunta
        await _show_faq_by_index(update, context, 0, bot_id)
        return
    
    # Si no hay FAQs, mostrar mensaje de error
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
        else:
            logger.warning(f"No se pudo editar el mensaje a faq_menu: {e}. Enviando uno nuevo.")
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=texto,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )

async def _show_faq_by_index(update: Update, context: ContextTypes.DEFAULT_TYPE, index: int, bot_id: int) -> None:
    """Muestra una FAQ específica por su índice"""
    items = context.user_data.get('faqs_list', [])
    
    if not items or index < 0 or index >= len(items):
        texto = "❌ Error: No se pudo cargar la pregunta."
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Menú Principal", callback_data='main_menu')]
        ])
    else:
        item = items[index]
        item_id = item['id']
        
        # Obtener el contenido completo de la FAQ
        item_details = await content_db.get_item_details(item_id, 'faqs', 'question', 'answer')
        
        if not item_details:
            texto = "❌ Contenido no encontrado."
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menú Principal", callback_data='main_menu')]
            ])
        else:
            question = item_details.get('title', 'Pregunta')
            answer = item_details.get('content', 'Respuesta no disponible')
            
            # Formatear el mensaje con pregunta y respuesta
            texto = f"❓ <b>{escape_html(question)}</b>\n\n{answer}\n\n<i>Pregunta {index + 1} de {len(items)}</i>"
            
            # Crear teclado con flechas de navegación
            reply_markup = await _get_faq_navigation_keyboard(index, len(items))
    
    # Actualizar el índice actual
    context.user_data['faq_current_index'] = index
    
    # Editar o enviar el mensaje
    query = update.callback_query
    if query:
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
            else:
                logger.warning(f"No se pudo editar el mensaje de FAQ: {e}. Enviando uno nuevo.")
                await context.bot.send_message(
                    chat_id=query.message.chat.id,
                    text=texto,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
    else:
        # Si no hay query (llamada directa), enviar nuevo mensaje
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=texto,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

async def _get_faq_navigation_keyboard(current_index: int, total_items: int):
    """Crea el teclado de navegación para FAQs"""
    keyboard = []
    
    # Fila 1: Botones de navegación (Anterior | Siguiente)
    nav_buttons = []
    
    # Botón Anterior (solo si no es la primera)
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="faq_prev"))
    else:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data="faq_ignore"))  # Deshabilitado
    
    # Botón Siguiente (solo si no es la última)
    if current_index < total_items - 1:
        nav_buttons.append(InlineKeyboardButton("Siguiente ➡️", callback_data="faq_next"))
    else:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data="faq_ignore"))  # Deshabilitado
    
    keyboard.append(nav_buttons)
    
    # Fila 2: Botón Home
    keyboard.append([InlineKeyboardButton("🏠 Menú Principal", callback_data='main_menu')])
    
    return InlineKeyboardMarkup(keyboard)

async def navigate_faq_previous(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Navega a la pregunta anterior"""
    query = update.callback_query
    await query.answer()
    
    current_index = context.user_data.get('faq_current_index', 0)
    items = context.user_data.get('faqs_list', [])
    
    if not items or current_index <= 0:
        await query.answer("Ya estás en la primera pregunta.", show_alert=True)
        return
    
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        bot_id = 1
    
    new_index = current_index - 1
    await _show_faq_by_index(update, context, new_index, bot_id)

async def navigate_faq_next(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Navega a la siguiente pregunta"""
    query = update.callback_query
    await query.answer()
    
    current_index = context.user_data.get('faq_current_index', 0)
    items = context.user_data.get('faqs_list', [])
    
    if not items or current_index >= len(items) - 1:
        await query.answer("Ya estás en la última pregunta.", show_alert=True)
        return
    
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        bot_id = 1
    
    new_index = current_index + 1
    await _show_faq_by_index(update, context, new_index, bot_id)

async def faq_ignore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ignora el callback cuando se presiona una flecha deshabilitada"""
    query = update.callback_query
    await query.answer("Ya estás en el límite.", show_alert=True)

# Esta función ya no se usa, pero la mantenemos por compatibilidad
async def show_faq_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Función legacy - ya no se usa, redirige al nuevo sistema"""
    await show_faqs_menu(update, context)
# --- CONVERSATION HANDLER PARA ENVIAR PREGUNTA AL ADMIN ---
async def ask_own_question_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✍️ Por favor, escribe tu pregunta a continuación. Será enviada de forma privada al especialista.\n\n"
        "Pulsa /cancelar si cambias de opinión."
    )
    return AWAITING_QUESTION

async def forward_question_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe la pregunta y la reenvía al administrador del bot."""
    user_question = update.message.text
    user = update.effective_user
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        bot_id = 1  # Fallback a SuperAdmin

    try:
        previous_message_id = update.message.message_id - 1
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=previous_message_id)
        await update.message.delete()
    except Exception as e:
        logger.warning(f"No se pudo borrar un mensaje durante la limpieza de 'ask_question': {e}")

    # --- ¡LLAMADA CORREGIDA! ---
    # Ahora usamos el módulo 'user_db'
    admin_id = await user_db.get_bot_admin_id(bot_id)

    if not admin_id:
        logger.error(f"No se pudo encontrar el admin_id para el bot {bot_id} al reenviar pregunta.")
        await update.effective_chat.send_message("❌ Hubo un error al enviar tu pregunta. Por favor, intenta más tarde.")
        return ConversationHandler.END

    user_mention = user.mention_html()
    notification_text = (
        f"📩 <b>Nueva pregunta de un usuario:</b>\n\n"
        f"<b>De:</b> {user_mention} (ID: <code>{user.id}</code>)\n\n"
        f"<b>Pregunta:</b>\n"
        f"<blockquote>{escape_html(user_question)}</blockquote>\n\n"
        f"Puedes contactarlo directamente haciendo clic en su nombre."
    )

    try:
        await context.bot.send_message(chat_id=admin_id, text=notification_text)
        await update.effective_chat.send_message(
            "✅ ¡Tu pregunta ha sido enviada con éxito!",
            reply_markup=get_return_to_main_menu_keyboard()
        )
    except Exception as e:
        logger.error(f"Error al enviar pregunta al admin {admin_id}: {e}")
        await update.effective_chat.send_message(
            "❌ Lo siento, hubo un problema al enviar tu pregunta.",
            reply_markup=get_return_to_main_menu_keyboard()
        )

    return ConversationHandler.END


async def cancel_question_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    from main import handle_all_callbacks
    await update.message.reply_text("Operación cancelada.")
    # Simular callback para volver al menú principal
    fake_query = type('obj', (object,), {'data': 'main_menu', 'message': update.message, 'answer': lambda *a, **k: None})()
    fake_update = type('obj', (object,), {'callback_query': fake_query, 'effective_user': update.effective_user})()
    await handle_all_callbacks(fake_update, context)
    return ConversationHandler.END

def register(app: Application):
    # Handler principal para mostrar FAQs (nuevo sistema con navegación)
    app.add_handler(CallbackQueryHandler(show_faqs_menu, pattern='^(faq|faq_menu|doctor_faq|patient_faq)$'))
    # Handlers de navegación
    app.add_handler(CallbackQueryHandler(navigate_faq_previous, pattern='^faq_prev$'))
    app.add_handler(CallbackQueryHandler(navigate_faq_next, pattern='^faq_next$'))
    app.add_handler(CallbackQueryHandler(faq_ignore, pattern='^faq_ignore$'))
    # Handler legacy (por compatibilidad)
    app.add_handler(CallbackQueryHandler(show_faq_content, pattern='^faq_item_'))