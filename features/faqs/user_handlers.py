"""
Handlers de usuario para ver FAQs – refactor multi-tenant.
Sin cambiar nombre de archivo para no romper imports.
"""
import logging
from telegram import Update, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.error import BadRequest
from common.helpers import escape_html
from common.context_manager import get_tenant_id
from .faq_service import list_faqs, get_faq   # mismo nombre

logger = logging.getLogger(__name__)

# ---------- MENÚ USUARIO ----------
async def show_faqs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await query.answer("No se pudo determinar el perfil.", show_alert=True)
        return
    items = await list_faqs(bot_id)
    if not items:
        await query.answer("No hay FAQs.", show_alert=True)
        return
    kb = [[IKB(q["question"], callback_data=f"faq_view_{q['id']}")] for q in items] + [[IKB("🏠 Menú Principal", callback_data="main_menu")]]
    await query.edit_message_text("❓ Preguntas Frecuentes", reply_markup=IKM(kb))

# ---------- VER FAQ ----------
async def faq_user_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    faq_id = int(query.data.split("_")[-1])
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await query.answer("Error de perfil.", show_alert=True)
        return
    faq = await get_faq(faq_id, bot_id)
    if not faq:
        await query.answer("FAQ no encontrada.", show_alert=True)
        return
    text = f"❓ <b>{escape_html(faq['question'])}</b>\n\n{faq['answer']}"
    kb = IKM([[IKB("🔙 Volver", callback_data="faq_menu")]])
    try:
        await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")
    except BadRequest as e:
        if "no text" in str(e).lower():
            await query.message.delete()
            await context.bot.send_message(query.message.chat.id, text, reply_markup=kb, parse_mode="HTML")

# ---------- REGISTRO (mismos nombres) ----------
def register(app):
    app.add_handler(CallbackQueryHandler(show_faqs_menu, pattern="^faq_menu$"))
    app.add_handler(CallbackQueryHandler(faq_user_view, pattern="^faq_view_\\d+$"))