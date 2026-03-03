# features/welcome_message/handlers.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.error import BadRequest
from telegram.constants import ParseMode

from database import content_db, user_db
from common.context_manager import get_tenant_id
from common.helpers import escape_html
from common.keyboards import get_back_to_menu_keyboard
from utils.role_manager import RoleManager
from config import DB_PATH
import aiosqlite
from handlers.callback_router import handle_all_callbacks

# Importación diferida para evitar circularidad si es necesario, pero B1 dice al TOP
# Si show_doctor_panel causa circularidad, usaremos import completo en el top
from features.main_menu.user_handler import show_doctor_panel

logger = logging.getLogger(__name__)

# Estados del ConversationHandler
AWAITING_WELCOME_MESSAGE = 1

async def show_edit_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el mensaje de bienvenida actual y permite editarlo"""
    query = update.callback_query
    await query.answer()
    
    bot_id = await get_tenant_id(update, context)
    if not bot_id:
        await query.answer("❌ Error: No se pudo obtener el tenant ID.", show_alert=True)
        return
    
    # Obtener mensaje actual
    current_message = await content_db.get_content("msg_bienvenida_editable", bot_id)
    if not current_message:
        current_message = "Bienvenido/a a mi consulta."
    
    text = (
        f"✏️ <b>Editar Mensaje de Bienvenida</b>\n\n"
        f"<b>Mensaje actual:</b>\n"
        f"<blockquote>{escape_html(current_message)}</blockquote>\n\n"
        f"📝 <b>Envía el nuevo mensaje de bienvenida:</b>\n"
        f"(Puedes usar HTML para formato: &lt;b&gt;negrita&lt;/b&gt;, &lt;i&gt;cursiva&lt;/i&gt;)\n\n"
        f"Usa /cancelar para cancelar."
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Volver", callback_data="cancel_edit_welcome")]
    ])
    
    try:
        msg = await query.edit_message_text(
            text=text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        context.user_data['welcome_message_id'] = msg.message_id
        context.user_data['welcome_chat_id'] = msg.chat_id
    except BadRequest as e:
        if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
            try:
                await query.message.delete()
            except:
                pass
            msg = await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            context.user_data['welcome_message_id'] = msg.message_id
            context.user_data['welcome_chat_id'] = msg.chat_id
        else:
            logger.warning(f"Error al editar mensaje de bienvenida: {e}")
            msg = await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            context.user_data['welcome_message_id'] = msg.message_id
            context.user_data['welcome_chat_id'] = msg.chat_id
    
    return AWAITING_WELCOME_MESSAGE

async def receive_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe y guarda el nuevo mensaje de bienvenida"""
    user_id = update.effective_user.id
    
    # Obtener bot_id de forma más directa para inquilinos
    role_manager = RoleManager(DB_PATH)
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    
    if doctor:
        # Si es un doctor, obtener su bot_id desde user_tenants
        bot_id = await user_db.get_user_tenant(user_id)
        if not bot_id:
            # Si no tiene bot_id en user_tenants, buscar en bots por admin_user_id
            async with aiosqlite.connect(DB_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(
                    'SELECT id FROM bots WHERE admin_user_id = ?',
                    (user_id,)
                )
                result = await cursor.fetchone()
                if result:
                    bot_id = result['id']
                else:
                    logger.error(f"No se encontró bot_id para doctor {user_id}")
                    await update.message.reply_text("❌ Error: No se pudo obtener el tenant ID.")
                    return ConversationHandler.END
    else:
        # Si no es doctor, usar get_tenant_id normal
        bot_id = await get_tenant_id(update, context)
        if not bot_id:
            logger.error("No se pudo obtener bot_id para actualizar mensaje de bienvenida")
            await update.message.reply_text("❌ Error: No se pudo obtener el tenant ID.")
            return ConversationHandler.END
    
    new_message = update.message.text.strip()  # Limpiar espacios al inicio y final
    logger.info(f"Actualizando mensaje de bienvenida para bot_id={bot_id}, user_id={user_id}, mensaje={new_message[:50]}...")
    logger.info(f"Longitud del mensaje recibido: {len(new_message)}")
    
    # Obtener el mensaje actual de la BD para comparar
    current_message = await content_db.get_content("msg_bienvenida_editable", bot_id)
    if current_message and current_message in new_message and new_message != current_message:
        # Si el mensaje nuevo contiene el mensaje viejo, eliminarlo
        new_message = new_message.replace(current_message, "").strip()
        logger.warning(f"⚠️ Se detectó mensaje viejo en el mensaje recibido, eliminado. Mensaje viejo: '{current_message[:50]}...', Nuevo mensaje: '{new_message[:50]}...'")
    
    # Verificar si el mensaje contiene el mensaje por defecto y eliminarlo si está presente
    mensaje_por_defecto = "Bienvenido/a a mi consulta."
    if mensaje_por_defecto in new_message:
        # Si el mensaje contiene el mensaje por defecto, eliminarlo
        new_message = new_message.replace(mensaje_por_defecto, "").strip()
        logger.warning(f"⚠️ Se detectó mensaje por defecto en el mensaje recibido, eliminado. Nuevo mensaje: '{new_message[:50]}...'")
    
    # Guardar el mensaje
    try:
        await content_db.update_content("msg_bienvenida_editable", new_message, bot_id)
        logger.info(f"✅ Mensaje de bienvenida guardado correctamente para bot_id={bot_id}")
        
        # Verificar que se guardó correctamente
        saved_message = await content_db.get_content("msg_bienvenida_editable", bot_id)
        if saved_message != new_message:
            logger.error(f"❌ El mensaje no se guardó correctamente. Esperado: {new_message[:50]}, Obtenido: {saved_message[:50] if saved_message else 'None'}")
        else:
            logger.info(f"✅ Verificación: El mensaje se guardó correctamente")
    except Exception as e:
        logger.error(f"❌ Error al guardar mensaje de bienvenida: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error al guardar el mensaje: {e}")
        return ConversationHandler.END
    
    # Confirmar
    text = (
        f"✅ <b>Mensaje de bienvenida actualizado</b>\n\n"
        f"<b>Nuevo mensaje:</b>\n"
        f"<blockquote>{escape_html(new_message)}</blockquote>"
    )
    
    # Determinar el callback de retorno según el rol
    user_id = update.effective_user.id
    role_manager = RoleManager(DB_PATH)
    user_role = await role_manager.get_user_role(user_id)
    
    if user_role == 'superadmin':
        back_callback = "main_menu"
    else:
        back_callback = "doctor_panel"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Volver", callback_data=back_callback)]
    ])
    
    await update.message.reply_text(
        text=text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    
    # Eliminar el mensaje anterior de la conversación
    try:
        await update.message.delete()
        if update.message.message_id > 1:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id - 1
            )
    except:
        pass
    
    return ConversationHandler.END

async def cancel_edit_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la edición del mensaje de bienvenida"""
    query = update.callback_query
    if query:
        await query.answer()
    
    # Si es un comando, intentar borrar el mensaje del comando
    if update.message:
        try:
            await update.message.delete()
        except:
            pass
    
    role_manager = RoleManager(DB_PATH)
    user_role = await role_manager.get_user_role(user_id)
    
    if user_role == 'superadmin':
        msg = query.message if query else update.effective_message
        fake_query = type('obj', (object,), {
            'data': 'main_menu',
            'message': msg,
            'answer': lambda *a, **k: None,
            'edit_message_text': msg.edit_text if msg else None,
            'edit_message_media': msg.edit_media if msg else None
        })()
        fake_update = type('obj', (object,), {
            'message': None,
            'callback_query': fake_query,
            'effective_user': update.effective_user,
            'effective_chat': update.effective_chat,
            'effective_message': msg
        })()
        await handle_all_callbacks(fake_update, context)
    else:
        # Si no hay query (es comando) y tenemos el ID del mensaje anterior,
        # construimos un fake update para que show_doctor_panel edite ese mensaje
        if not query and context.user_data.get('welcome_message_id'):
            chat_id = context.user_data.get('welcome_chat_id')
            message_id = context.user_data.get('welcome_message_id')
            
            # Clases fake para simular la estructura necesaria
            class FakeMessage:
                def __init__(self, bot, chat_id, message_id):
                    self.bot = bot
                    self.chat_id = chat_id
                    self.message_id = message_id
                    self.chat = type('obj', (object,), {'id': chat_id})
                
                async def edit_text(self, *args, **kwargs):
                    return await self.bot.edit_message_text(chat_id=self.chat_id, message_id=self.message_id, *args, **kwargs)

            class FakeQuery:
                def __init__(self, message):
                    self.message = message
                    self.data = "doctor_panel"
                
                async def answer(self, *args, **kwargs):
                    pass
                
                async def edit_message_text(self, *args, **kwargs):
                    return await self.message.edit_text(*args, **kwargs)

            fake_msg = FakeMessage(context.bot, chat_id, message_id)
            fake_query = FakeQuery(fake_msg)
            
            fake_update = type('obj', (object,), {
                'callback_query': fake_query,
                'effective_user': update.effective_user,
                'effective_chat': update.effective_chat,
                'message': None
            })()
            
            await show_doctor_panel(fake_update, context)
        else:
            await show_doctor_panel(update, context)
    
    return ConversationHandler.END

def register(app):
    """Registra los handlers para editar el mensaje de bienvenida"""
    edit_welcome_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(show_edit_welcome_message, pattern='^edit_welcome_message$')
        ],
        states={
            AWAITING_WELCOME_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_welcome_message)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_edit_welcome, pattern='^cancel_edit_welcome$'),
            MessageHandler(filters.COMMAND, cancel_edit_welcome)
        ],
        allow_reentry=True
    )
    app.add_handler(edit_welcome_conv)

