from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from database.session import get_session
from database.repositories.bot_repository import BotRepository
from utils.role_manager import RoleManager
from config import DB_PATH
import logging

logger = logging.getLogger(__name__)
role_manager = RoleManager(DB_PATH)

# Estados de la conversación
AWAITING_LOGO = 1

async def branding_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menú principal de branding."""
    logger.info(f"Entrando a branding_hub para usuario {update.effective_user.id}")
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🖼️ Cambiar Logo", callback_data="change_logo")],
        [InlineKeyboardButton("🗑️ Eliminar Logo", callback_data="delete_logo")],
        [InlineKeyboardButton("🏠 Volver al Panel", callback_data="doctor_panel")]
    ]
    
    text = (
        "<b>🎭 Identidad Visual</b>\n\n"
        "Aquí puedes personalizar la imagen que ven tus pacientes al iniciar el bot.\n\n"
        "<i>Tu logo actual se mostrará en el menú principal y en la sección informativa.</i>"
    )
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return ConversationHandler.END

async def start_change_logo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el flujo de cambio de logo."""
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("❌ Cancelar", callback_data="cancel_branding")]]
    
    await query.edit_message_text(
        "📸 <b>Envía la nueva imagen para tu bot.</b>\n\n"
        "Se recomienda una imagen cuadrada o rectangular de buena calidad.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return AWAITING_LOGO

async def handle_logo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa la imagen subida por el doctor."""
    user_id = update.effective_user.id
    photo = update.message.photo[-1] # La mejor calidad
    file_id = photo.file_id
    
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    if not doctor:
        await update.message.reply_text("❌ No se encontró un bot asociado a tu cuenta.")
        return ConversationHandler.END
    bot_id = doctor[0]
        
    async with get_session() as session:
        repo = BotRepository(session)
        success = await repo.update_logo(bot_id, file_id, "photo")
        
    if success:
        await update.message.reply_text(
            "✅ <b>Logo actualizado correctamente.</b>\n\n"
            "Tus pacientes ahora verán esta imagen al iniciar el bot.",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("❌ Hubo un error al actualizar el logo. Por favor, intenta de nuevo.")
        
    return ConversationHandler.END

async def delete_logo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Elimina el logo personalizado."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    if not doctor:
        await query.edit_message_text("❌ No se encontró un bot asociado a tu cuenta.")
        return ConversationHandler.END
    bot_id = doctor[0]
    
    async with get_session() as session:
        repo = BotRepository(session)
        success = await repo.update_logo(bot_id, None, "photo")
        
    if success:
        await query.edit_message_text("✅ Logo eliminado. El bot volverá a usar la imagen por defecto.")
    else:
        await query.edit_message_text("❌ Error al eliminar el logo.")
    return ConversationHandler.END

async def cancel_branding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela el flujo de branding."""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("Operación cancelada.")
    else:
        await update.message.reply_text("Operación cancelada.")
    return ConversationHandler.END

branding_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(branding_hub, pattern="^branding_hub$"),
        CallbackQueryHandler(start_change_logo, pattern="^change_logo$"),
        CallbackQueryHandler(delete_logo, pattern="^delete_logo$")
    ],
    states={
        AWAITING_LOGO: [
            MessageHandler(filters.PHOTO, handle_logo_upload),
            CallbackQueryHandler(cancel_branding, pattern="^cancel_branding$")
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel_branding)],
    name="branding_conversation",
    persistent=True,
    allow_reentry=True
)
