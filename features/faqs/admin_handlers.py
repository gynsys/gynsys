"""
Handlers de administración de FAQs usando arquitectura workflow.
Separado por tipo de usuario:
- Superadmin: Puede gestionar FAQs de todos los tenants
- Tenants (Doctores): Gestionan sus propias FAQs
"""
import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from telegram.ext import (
    Application,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CommandHandler
)

from database import content_db
from common.decorators import admin_required
from common.helpers import escape_html
from common.keyboards import get_delete_confirmation_keyboard
from common.conversation_utils import cancel_conv
from .workflow import FAQWorkflow, WorkflowState
from . import keyboards as admin_keyboards

logger = logging.getLogger(__name__)

CONFIG = {
    'singular': 'FAQ',
    'plural': 'FAQs',
    'prefix': 'faq'
}


# ==================== HUB PRINCIPAL ====================
@admin_required
async def faqs_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hub principal de gestión de FAQs"""
    query = update.callback_query
    if query:
        await query.answer()
    
    bot_id = await FAQWorkflow.get_bot_id(update, context)
    if not bot_id:
        error_msg = "❌ No se pudo determinar el perfil del médico."
        if query:
            await query.edit_message_text(error_msg, parse_mode="HTML")
        else:
            await update.effective_message.reply_text(error_msg)
        return
    
    keyboard = [
        [InlineKeyboardButton(f"✏️ Editar Encabezado", callback_data="faq_edit_header")],
        [InlineKeyboardButton(f"➕ Añadir {CONFIG['singular']}", callback_data="faq_add_start")],
        [InlineKeyboardButton(f"✏️ Modificar {CONFIG['singular']}", callback_data="faq_modify_list")],
        [InlineKeyboardButton(f"🗑️ Eliminar {CONFIG['singular']}", callback_data="faq_delete_list")],
        [
            InlineKeyboardButton("🔙 Volver", callback_data='doctor_panel'),
            InlineKeyboardButton("🏠 Menú Principal", callback_data='main_menu')
        ]
    ]
    
    text = f"🔧 <b>Gestión de {CONFIG['plural']}</b>"
    
    if query:
        try:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error editando mensaje: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML"
            )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )


# ==================== AGREGAR FAQ ====================
@admin_required
async def start_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Inicia el flujo de agregar FAQ"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['workflow_state'] = WorkflowState.AWAITING_QUESTION
    context.user_data['main_message_id'] = query.message.message_id
    
    await query.edit_message_text(
        f"✍️ Envía la <b>pregunta</b> para la nueva {CONFIG['singular']}.\n\n"
        f"<i>/cancelar para detener.</i>",
        parse_mode="HTML"
    )
    return WorkflowState.AWAITING_QUESTION


async def receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Recibe la pregunta del usuario"""
    question = update.message.text.strip()
    
    if not question:
        await update.message.reply_text("❌ La pregunta no puede estar vacía. Intenta nuevamente:")
        return WorkflowState.AWAITING_QUESTION
    
    context.user_data['new_question'] = question
    context.user_data['workflow_state'] = WorkflowState.AWAITING_ANSWER
    
    try:
        await update.message.delete()
    except Exception:
        pass
    
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['main_message_id'],
        text="✅ Pregunta guardada. Ahora, envía la <b>respuesta</b>.",
        parse_mode="HTML"
    )
    return WorkflowState.AWAITING_ANSWER


async def receive_answer_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe la respuesta y guarda la FAQ"""
    answer = update.message.text_html if hasattr(update.message, 'text_html') else update.message.text
    
    if not answer or answer.strip() == '':
        await update.message.reply_text("❌ La respuesta no puede estar vacía. Intenta nuevamente:")
        return WorkflowState.AWAITING_ANSWER
    
    question = context.user_data.get('new_question')
    if not question:
        await update.message.reply_text("❌ Error: No se encontró la pregunta. Por favor, inicia nuevamente.")
        return ConversationHandler.END
    
    # Usar workflow para agregar
    result = await FAQWorkflow.handle_add_workflow(update, context, question, answer)
    
    if not result['success']:
        await update.message.reply_text(f"❌ Error: {result.get('error', 'No se pudo guardar la FAQ')}")
        return ConversationHandler.END
    
    try:
        await update.message.delete()
    except Exception:
        pass
    
    # Mostrar éxito y redirigir
    message_to_edit = await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data.pop('main_message_id', None),
        text=f"✅ ¡{CONFIG['singular']} añadida con éxito!"
    )
    await asyncio.sleep(2)
    
    # Limpiar estado
    context.user_data.pop('new_question', None)
    context.user_data.pop('workflow_state', None)
    
    # Redirigir a lista de modificación para ver el resultado
    await FAQWorkflow.redirect_to_list(update, context, "modify", message_to_edit)
    return ConversationHandler.END


# ==================== MODIFICAR FAQ ====================
@admin_required
async def start_modify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Inicia el flujo de modificar FAQ"""
    query = update.callback_query
    await query.answer()
    
    faq_id = int(query.data.split('_')[-1])
    bot_id = await FAQWorkflow.get_bot_id(update, context)
    
    if not bot_id:
        await query.edit_message_text("❌ No se pudo determinar el perfil del médico.")
        return ConversationHandler.END
    
    # Obtener FAQ usando workflow
    result = await FAQWorkflow.handle_get_workflow(update, context, faq_id)
    
    if not result['success']:
        await query.edit_message_text(f"❌ {result.get('error', 'FAQ no encontrada')}")
        return ConversationHandler.END
    
    faq = result['faq']
    
    # Guardar estado
    context.user_data['workflow_state'] = WorkflowState.AWAITING_MOD_QUESTION
    context.user_data['faq_id'] = faq_id
    context.user_data['original_faq'] = faq
    context.user_data['main_message_id'] = query.message.message_id
    
    await query.edit_message_text(
        f"✏️ Modificando '{escape_html(faq['title'])}'.\n\n"
        f"<b>Pregunta actual:</b>\n<blockquote>{escape_html(faq['title'])}</blockquote>\n"
        f"Envía la <b>nueva pregunta</b> o '.' para mantener.\n\n"
        f"<i>/cancelar para detener.</i>",
        parse_mode="HTML"
    )
    return WorkflowState.AWAITING_MOD_QUESTION


async def receive_mod_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Recibe la nueva pregunta"""
    new_question = update.message.text.strip() if update.message.text != '.' else None
    
    if new_question:
        context.user_data['new_question'] = new_question
    
    context.user_data['workflow_state'] = WorkflowState.AWAITING_MOD_ANSWER
    original_faq = context.user_data['original_faq']
    
    try:
        await update.message.delete()
    except Exception:
        pass
    
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['main_message_id'],
        text=(
            f"<b>Respuesta actual:</b>\n<blockquote>{escape_html(original_faq['content'])}</blockquote>\n"
            f"Envía la <b>nueva respuesta</b> o '.' para mantener."
        ),
        parse_mode="HTML"
    )
    return WorkflowState.AWAITING_MOD_ANSWER


async def receive_mod_answer_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe la nueva respuesta y guarda los cambios"""
    new_answer = None
    user_text = update.message.text if update.message.text else ""
    
    if user_text != '.':
        new_answer = update.message.text_html if hasattr(update.message, 'text_html') else user_text
    
    faq_id = context.user_data.get('faq_id')
    new_question = context.user_data.get('new_question')
    
    if not faq_id:
        await update.message.reply_text("❌ Error: No se encontró el ID de la FAQ.")
        return ConversationHandler.END
    
    # Usar workflow para actualizar
    result = await FAQWorkflow.handle_update_workflow(
        update,
        context,
        faq_id,
        new_question,
        new_answer
    )
    
    if not result['success']:
        await update.message.reply_text(f"❌ Error: {result.get('error', 'No se pudo actualizar la FAQ')}")
        return ConversationHandler.END
    
    try:
        await update.message.delete()
    except Exception:
        pass
    
    # Mostrar éxito y redirigir
    message_to_edit = await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data.pop('main_message_id', None),
        text=f"✅ ¡{CONFIG['singular']} actualizado con éxito!"
    )
    await asyncio.sleep(2)
    
    # Limpiar estado
    context.user_data.pop('faq_id', None)
    context.user_data.pop('original_faq', None)
    context.user_data.pop('new_question', None)
    context.user_data.pop('workflow_state', None)
    
    # Redirigir a lista de modificación
    await FAQWorkflow.redirect_to_list(update, context, "modify", message_to_edit)
    return ConversationHandler.END


# ==================== ELIMINAR FAQ ====================
@admin_required
async def list_for_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista FAQs para eliminar"""
    query = update.callback_query
    await query.answer()
    
    result = await FAQWorkflow.handle_list_workflow(update, context, "delete")
    
    if not result['success']:
        await query.answer(result.get('error', 'No hay FAQs para eliminar'), show_alert=True)
        return
    
    await query.edit_message_text(
        f"Selecciona la {CONFIG['singular'].lower()} que deseas eliminar:",
        reply_markup=result['keyboard']
    )


@admin_required
async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma la eliminación de una FAQ"""
    query = update.callback_query
    await query.answer()
    
    faq_id = int(query.data.split('_')[-1])
    
    # Obtener detalles usando workflow
    result = await FAQWorkflow.handle_get_workflow(update, context, faq_id)
    
    if not result['success']:
        await query.edit_message_text(f"❌ {result.get('error', 'FAQ no encontrada')}")
        return
    
    faq = result['faq']
    item_name = escape_html(faq['title'])
    
    callback_confirm = f"faq_delete_execute_confirm_{faq_id}"
    
    await query.edit_message_text(
        f"<b>⚠️ ¿Seguro que quieres eliminar?</b>\n\n<blockquote>{item_name}</blockquote>",
        reply_markup=get_delete_confirmation_keyboard(
            item_type_callback=callback_confirm,
            back_callback="faq_delete_list"
        ),
        parse_mode="HTML"
    )


@admin_required
async def execute_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta la eliminación de una FAQ"""
    query = update.callback_query
    await query.answer()
    
    faq_id = int(query.data.split('_')[-1])
    
    # Usar workflow para eliminar
    result = await FAQWorkflow.handle_delete_workflow(update, context, faq_id)
    
    if not result['success']:
        await query.answer(result.get('error', 'No se pudo eliminar'), show_alert=True)
        return
    
    await query.answer("✅ Elemento eliminado.", show_alert=True)
    
    # Redirigir a lista de eliminación actualizada
    await FAQWorkflow.redirect_to_list(update, context, "delete", query.message)


# ==================== LISTAR PARA MODIFICAR ====================
@admin_required
async def list_for_modify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista FAQs para modificar"""
    query = update.callback_query
    await query.answer()
    
    result = await FAQWorkflow.handle_list_workflow(update, context, "modify")
    
    if not result['success']:
        await query.answer(result.get('error', 'No hay FAQs para modificar'), show_alert=True)
        return
    
    await query.edit_message_text(
        f"Selecciona la {CONFIG['singular'].lower()} que deseas modificar:",
        reply_markup=result['keyboard']
    )


# ==================== EDITAR ENCABEZADO ====================
@admin_required
async def start_edit_header(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Inicia la edición del encabezado"""
    query = update.callback_query
    await query.answer()
    
    bot_id = await FAQWorkflow.get_bot_id(update, context)
    if not bot_id:
        await query.edit_message_text("❌ No se pudo determinar el perfil del médico.")
        return ConversationHandler.END
    
    context.user_data['workflow_state'] = WorkflowState.AWAITING_HEADER
    context.user_data['main_message_id'] = query.message.message_id
    
    current_header = await content_db.get_content("header_faq", bot_id) or "(Sin encabezado definido)"
    
    await query.edit_message_text(
        f"✍️ Editando encabezado para <b>{CONFIG['plural']}</b>\n\n"
        f"<b>Texto actual:</b>\n<blockquote>{current_header}</blockquote>\n\n"
        f"Envía el nuevo texto del encabezado.\n\n<i>/cancelar para detener.</i>",
        parse_mode="HTML"
    )
    return WorkflowState.AWAITING_HEADER


async def save_header(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guarda el nuevo encabezado"""
    new_header = update.message.text_html if hasattr(update.message, 'text_html') else update.message.text
    bot_id = await FAQWorkflow.get_bot_id(update, context)
    
    if not bot_id:
        await update.message.reply_text("❌ No se pudo determinar el perfil del médico.")
        return ConversationHandler.END
    
    await content_db.update_content("header_faq", new_header, bot_id)
    
    try:
        await update.message.delete()
    except Exception:
        pass
    
    message_to_edit = await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data.pop('main_message_id', None),
        text="✅ Encabezado actualizado."
    )
    await asyncio.sleep(2)
    
    context.user_data.pop('workflow_state', None)
    
    # Redirigir al hub
    await FAQWorkflow.redirect_to_hub(update, context)
    return ConversationHandler.END


# ==================== REGISTRO DE HANDLERS ====================
def register(app: Application):
    """Registra todos los handlers de FAQs"""
    cancel_handlers = [
        CommandHandler('cancelar', cancel_conv),
        CallbackQueryHandler(cancel_conv, pattern='^cancel_conv$')
    ]
    
    # ConversationHandler para agregar
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add, pattern='^faq_add_start$')],
        states={
            WorkflowState.AWAITING_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_question)
            ],
            WorkflowState.AWAITING_ANSWER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answer_and_save)
            ]
        },
        fallbacks=cancel_handlers,
        allow_reentry=True
    )
    
    # ConversationHandler para modificar
    modify_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_modify, pattern='^faq_modify_\\d+$')],
        states={
            WorkflowState.AWAITING_MOD_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_mod_question)
            ],
            WorkflowState.AWAITING_MOD_ANSWER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_mod_answer_and_save)
            ]
        },
        fallbacks=cancel_handlers,
        allow_reentry=True
    )
    
    # ConversationHandler para editar encabezado
    header_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_edit_header, pattern='^faq_edit_header$')],
        states={
            WorkflowState.AWAITING_HEADER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_header)
            ]
        },
        fallbacks=cancel_handlers,
        allow_reentry=True
    )
    
    # Handlers de callbacks
    app.add_handler(add_conv)
    app.add_handler(modify_conv)
    app.add_handler(header_conv)
    app.add_handler(CallbackQueryHandler(faqs_hub, pattern='^faqs_admin_hub$'))
    app.add_handler(CallbackQueryHandler(list_for_modify, pattern='^faq_modify_list$'))
    app.add_handler(CallbackQueryHandler(list_for_delete, pattern='^faq_delete_list$'))
    app.add_handler(CallbackQueryHandler(confirm_delete, pattern='^faq_delete_\\d+$'))
    app.add_handler(CallbackQueryHandler(execute_delete, pattern='^faq_delete_execute_confirm_\\d+$'))

