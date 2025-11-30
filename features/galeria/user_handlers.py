# features/galeria/user_handlers.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

from database import content_db
from common.context_manager import get_tenant_id
from .keyboards import get_galeria_keyboard
from common.keyboards import get_back_to_menu_keyboard # Asumiendo que existe
from common.helpers import cleanup_extra_messages

logger = logging.getLogger(__name__)



async def show_galeria_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Muestra el menú principal de la galería. Limpia los mensajes anteriores si es necesario.
    """
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    # 1. LIMPIEZA PRIMERO (Lógica de "Volver al menú") - Tomada del bot viejo
    await cleanup_extra_messages(context, chat_id)

    # 2. OBTENER DATOS Y CONSTRUIR EL MENÚ
    tenant_id = await get_tenant_id(update, context)
    if not tenant_id:
        # Editamos el mensaje actual (el de los botones de navegación)
        await query.message.edit_text("No se pudo identificar el contenido a mostrar.")
        return

    texto_header = await content_db.get_content('header_galeria', tenant_id) or '🖼️ <b>Galería de Contenido</b>'
    reply_markup = await get_galeria_keyboard(tenant_id)

    # 3. EDITAR EL MENSAJE ACTUAL PARA MOSTRAR EL MENÚ
    try:
        await query.message.edit_text(text=texto_header, reply_markup=reply_markup, parse_mode='HTML')
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.warning(f"No se pudo editar el mensaje a galeria_menu: {e}. Enviando uno nuevo.")
            # Borramos el mensaje viejo para evitar duplicados y enviamos el nuevo
            await query.message.delete()
            await context.bot.send_message(chat_id, text=texto_header, reply_markup=reply_markup, parse_mode='HTML')
async def show_galeria_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Muestra el contenido de un ítem, siguiendo la lógica del bot viejo para una UX limpia.
    """
    query = update.callback_query; await query.answer()
    chat_id = update.effective_chat.id
    item_id = int(query.data.split('_')[-1])

    item_details = await content_db.get_item_details_with_media(item_id, 'gallery', 'title', 'content')
    if not item_details:
        await query.answer("Contenido no disponible.", show_alert=True); return

    # --- LÓGICA DEL BOT VIEJO: delete -> send -> send -> send ---
    
    # 1. Borramos el mensaje del menú de la galería
    await query.message.delete()

    # 2. Preparamos para guardar los IDs de los nuevos mensajes que vamos a crear
    #context.user_data['gallery_extra_message_ids'] = []
    context.user_data['extra_message_ids'] = []
    # 3. Enviamos el texto largo como un mensaje nuevo
    texto_largo = item_details.get('content', '')
    if texto_largo:
        msg1 = await context.bot.send_message(chat_id=chat_id, text=texto_largo, parse_mode='HTML')
        context.user_data['extra_message_ids'].append(msg1.message_id)

    # 4. Enviamos la imagen/video como un mensaje nuevo
    media_file_id = item_details.get('media_file_id')
    media_type = item_details.get('media_type')
    if media_file_id:
        try:
            sender_func = context.bot.send_photo if media_type == 'photo' else context.bot.send_video
            media_msg = await sender_func(chat_id=chat_id, **{media_type: media_file_id})
            context.user_data['extra_message_ids'].append(media_msg.message_id)
        except Exception as e:
            logger.error(f"Error al enviar media de la galería: {e}")

    # 5. Enviamos el mensaje final con los botones de navegación
    texto_botones = "👇 Selecciona una opción:"
    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Volver", callback_data='galeria_menu')
            #InlineKeyboardButton("🏠", callback_data='main_menu')
        ]
    ])
    await context.bot.send_message(chat_id=chat_id, text=texto_botones, reply_markup=reply_markup)