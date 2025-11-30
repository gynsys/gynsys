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
from config import SUPER_ADMIN_ID

logger = logging.getLogger(__name__)

# ---------- MENÚ USUARIO ----------
async def show_faqs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await query.answer("No se pudo determinar el perfil.", show_alert=True)
        return
    
    try:
        items = await list_faqs(bot_id)
    except Exception as e:
        logger.error(f"Error listing FAQs: {e}")
        await query.answer("Error interno al cargar FAQs.", show_alert=True)
        return

    # Permitir ver el menú vacío si es admin para poder añadir
    user_id = update.effective_user.id
    is_superadmin = (user_id == SUPER_ADMIN_ID)
    
    if not items and not is_superadmin:
        await query.answer("No hay FAQs.", show_alert=True)
        return
        
    kb = [[IKB(q["question"], callback_data=f"faq_view_{q['id']}")] for q in items]
    
    kb.append([IKB("🏠 Menú Principal", callback_data="main_menu")])
    
    text = "❓ Preguntas Frecuentes"
    reply_markup = IKM(kb)
    
    try:
        await query.edit_message_text(text, reply_markup=reply_markup)
    except BadRequest:
        # Si falla (ej. es una foto), borrar y enviar nuevo
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=text,
            reply_markup=reply_markup
        )

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