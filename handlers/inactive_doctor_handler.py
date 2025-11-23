"""
Handler para médicos inactivos
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


async def show_inactive_doctor_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra mensaje para médicos inactivos
    """
    message = (
        "🔒 **Acceso Restringido - Renueva tu Bot**\n\n"
        "Tu suscripción ha expirado o has sido suspendido.\n\n"
        "📞 **Para reactivar tu acceso:**\n"
        "Contacta al administrador del sistema para renovar tu suscripción.\n\n"
        "💳 **Renueva hoy mismo** y continúa disfrutando de todos los beneficios."
    )
    
    keyboard = [
        [InlineKeyboardButton("📞 Contactar Soporte", url="https://t.me/tu_admin")],
        [InlineKeyboardButton("🔄 Reintentar", callback_data="retry_access")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

