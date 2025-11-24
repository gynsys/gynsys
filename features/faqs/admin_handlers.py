"""
Handlers de administración de FAQs – refactor multi-tenant.
Sin cambiar nombre de archivo para no romper imports.
"""
import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from telegram.ext import (
    Application, ConversationHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, CommandHandler
)
from common.decorators import admin_required
from common.conversation_utils import cancel_conv
from .workflow import FAQWorkflow, WorkflowState   # mismo nombre
from .keyboards import faqs_for_action_keyboard    # mismo nombre
from common.helpers import escape_html

logger = logging.getLogger(__name__)
CONFIG = dict(singular='FAQ', plural='FAQs', prefix='faq')

# ---------- HUB ----------
@admin_required
async def faqs_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kb = [
        [IKB("✏️ Editar Encabezado", callback_data="faq_edit_header")],
        [IKB(f"➕ Añadir {CONFIG['singular']}", callback_data="faq_add_start")],
        [IKB(f"✏️ Modificar {CONFIG['singular']}", callback_data="faq_modify_list")],
        [IKB(f"🗑️ Eliminar {CONFIG['singular']}", callback_data="faq_delete_list")],
        [IKB("🔙 Volver", callback_data='doctor_panel'), IKB("🏠 Menú Principal", callback_data='main_menu')]
    ]
    text = f"🔧 <b>Gestión de {CONFIG['plural']}</b>"
    await query.edit_message_text(text, reply_markup=IKM(kb), parse_mode="HTML")

# ---------- ADD ----------
AWAITING_QUESTION, AWAITING_ANSWER = range(2)

@admin_required
async def faq_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['main_message_id'] = query.message.message_id
    await query.edit_message_text("✍️ Envía la <b>pregunta</b>:", parse_mode="HTML")
    return AWAITING_QUESTION

async def faq_add_receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['faq_question'] = update.message.text.strip()
    try: await update.message.delete()
    except: pass
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['main_message_id'],
        text="✅ Ahora envía la <b>respuesta</b>:", parse_mode="HTML"
    )
    return AWAITING_ANSWER

async def faq_add_receive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # --- datos ---
    q = context.user_data.pop('faq_question', None)
    a = getattr(update.message, 'text_html', None) or update.message.text
    if not q:
        await update.message.reply_text("❌ Error interno.")
        return ConversationHandler.END

    # --- guardar ---
    res = await FAQWorkflow.handle_add_workflow(update, context, q, a)
    try:
        await update.message.delete()
    except:
        pass

    msg_id = context.user_data.pop('main_message_id')

    # 1. éxito
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=msg_id,
        text="✅ FAQ añadida con éxito."
    )

    # 2. tiempo para leer
    await asyncio.sleep(2)

    # 3. mismo mensaje → lista limpia (acción "modify" para que pueda seguir)
    list_res = await FAQWorkflow.handle_list_workflow(update, context, "modify")
    if list_res['success']:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg_id,
            text="Selecciona la FAQ que deseas modificar:",
            reply_markup=list_res['keyboard']
        )
    else:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg_id,
            text="No hay FAQs para modificar."
        )

    return ConversationHandler.END

# ---------- MODIFY ----------
AWAITING_MOD_QUESTION, AWAITING_MOD_ANSWER = range(2)

@admin_required
async def faq_modify_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    res = await FAQWorkflow.handle_list_workflow(update, context, "modify")
    if not res['success']:
        await query.answer(res['error'], show_alert=True)
        return
    await query.edit_message_text("Selecciona la FAQ a modificar:", reply_markup=res['keyboard'])

@admin_required
async def faq_modify_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    faq_id = int(query.data.split('_')[-1])
    res = await FAQWorkflow.handle_get_workflow(update, context, faq_id)
    if not res['success']:
        await query.answer(res['error'], show_alert=True)
        return ConversationHandler.END
    faq = res['faq']
    context.user_data.update({
        'faq_mod_id': faq_id,
        'faq_mod_q': faq['question'],
        'faq_mod_a': faq['answer'],
        'main_message_id': query.message.message_id
    })
    await query.edit_message_text(
        f"✏️ Pregunta actual:\n<blockquote>{escape_html(faq['question'])}</blockquote>\n"
        f"Envía la nueva pregunta o '.' para mantener:",
        parse_mode="HTML"
    )
    return AWAITING_MOD_QUESTION

async def faq_mod_receive_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['faq_new_q'] = None if update.message.text == '.' else update.message.text
    try: await update.message.delete()
    except: pass
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['main_message_id'],
        text=f"✅ Ahora envía la nueva respuesta o '.' para mantener:",
        parse_mode="HTML"
    )
    return AWAITING_MOD_ANSWER

async def faq_mod_receive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # --- datos ---
    faq_id = context.user_data.pop('faq_mod_id', None)
    old_q  = context.user_data.pop('faq_mod_q', None)
    old_a  = context.user_data.pop('faq_mod_a', None)
    new_q  = context.user_data.pop('faq_new_q', None)
    new_a  = None if update.message.text == '.' else getattr(update.message, 'text_html', None) or update.message.text
    if not faq_id or not old_q or not old_a:
        await update.message.reply_text("❌ Error interno.")
        return ConversationHandler.END

    # --- guardar ---
    res = await FAQWorkflow.handle_update_workflow(update, context, faq_id, new_q, new_a)
    try:
        await update.message.delete()
    except:
        pass

    msg_id = context.user_data.pop('main_message_id')

    # 1. éxito
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=msg_id,
        text="✅ FAQ actualizada con éxito."
    )

    # 2. tiempo para leer
    await asyncio.sleep(2)

    # 3. mismo mensaje → lista limpia
    list_res = await FAQWorkflow.handle_list_workflow(update, context, "modify")
    if list_res['success']:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg_id,
            text="Selecciona otra FAQ a modificar:",
            reply_markup=list_res['keyboard']
        )
    else:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg_id,
            text="No hay más FAQs para modificar."
        )

    return ConversationHandler.END

# ---------- DELETE ----------
@admin_required
async def faq_delete_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    res = await FAQWorkflow.handle_list_workflow(update, context, "delete")
    if not res['success']:
        await query.answer(res['error'], show_alert=True)
        return
    await query.edit_message_text("Selecciona la FAQ a eliminar:", reply_markup=res['keyboard'])

@admin_required
async def faq_delete_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    faq_id = int(query.data.split('_')[-1])
    res = await FAQWorkflow.handle_get_workflow(update, context, faq_id)
    if not res['success']:
        await query.answer(res['error'], show_alert=True)
        return
    from common.keyboards import get_delete_confirmation_keyboard
    kb = get_delete_confirmation_keyboard(f"faq_delete_execute_{faq_id}", "faq_delete_list")
    await query.edit_message_text(
        f"¿Seguro de eliminar?\n\n<blockquote>{escape_html(res['faq']['question'])}</blockquote>",
        reply_markup=kb, parse_mode="HTML"
    )

@admin_required
async def faq_delete_execute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    faq_id = int(query.data.split('_')[-1])
    res = await FAQWorkflow.handle_delete_workflow(update, context, faq_id)
    await query.answer("✅ Eliminada." if res['success'] else f"❌ Error: {res['error']}", show_alert=True)
    await faq_delete_list(update, context)

# ---------- REGISTRO (mismos nombres de siempre) ----------
def register(app: Application):
    from telegram.ext import ConversationHandler
    cancel = [CommandHandler("cancelar", cancel_conv), CallbackQueryHandler(cancel_conv, pattern="^cancel_conv$")]

    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(faq_add_start, pattern="^faq_add_start$")],
        states={
            AWAITING_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, faq_add_receive_question)],
            AWAITING_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, faq_add_receive_answer)]
        },
        fallbacks=cancel
    )

    mod_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(faq_modify_start, pattern="^faq_modify_\\d+$")],
        states={
            AWAITING_MOD_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, faq_mod_receive_question)],
            AWAITING_MOD_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, faq_mod_receive_answer)]
        },
        fallbacks=cancel
    )

    app.add_handler(add_conv)
    app.add_handler(mod_conv)
    app.add_handler(CallbackQueryHandler(faqs_hub, pattern="^faqs_admin_hub$"))
    app.add_handler(CallbackQueryHandler(faq_modify_list, pattern="^faq_modify_list$"))
    app.add_handler(CallbackQueryHandler(faq_delete_list, pattern="^faq_delete_list$"))
    app.add_handler(CallbackQueryHandler(faq_delete_confirm, pattern="^faq_delete_\\d+$"))
    app.add_handler(CallbackQueryHandler(faq_delete_execute, pattern="^faq_delete_execute_\\d+$"))