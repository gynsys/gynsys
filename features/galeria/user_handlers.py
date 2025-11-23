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

logger = logging.getLogger(__name__)

async def cleanup_gallery_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """
    Función de ayuda para limpiar los mensajes extra de la galería (texto e imagen)
    que se guardaron en el contexto del usuario.
    """
    if extra_ids := context.user_data.pop('gallery_extra_message_ids', None):
        for msg_id in extra_ids:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except BadRequest as e:
                # Ignorar errores si el mensaje ya fue borrado
                if "Message to delete not found" not in str(e):
                    logger.warning(f"No se pudo borrar el mensaje extra de galería {msg_id}: {e}")
            except Exception as e:
                logger.error(f"Error inesperado al borrar mensaje extra de galería {msg_id}: {e}")

async def show_galeria_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Muestra el menú principal de la galería.
    También se encarga de limpiar los mensajes de la vista de un ítem si se vuelve desde allí.
    """
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    # 1. LIMPIEZA PRIMERO (Lógica de "Volver al menú")
    # Si venimos de ver un ítem, limpiamos los mensajes sobrantes.
    await cleanup_gallery_messages(context, chat_id)

    # 2. OBTENER DATOS Y CONSTRUIR EL MENÚ
    tenant_id = await get_tenant_id(update, context)
    if not tenant_id:
        await query.message.edit_text("No se pudo identificar el contenido a mostrar.")
        return

    texto_header = await content_db.get_content('header_galeria', tenant_id) or '🖼️ <b>Galería de Contenido</b>'
    reply_markup = await get_galeria_keyboard(tenant_id)

    # 3. EDITAR EL MENSAJE ACTUAL PARA MOSTRAR EL MENÚ
    # Transición fluida: si es imagen, eliminar primero, luego editar
    try:
        await query.message.edit_text(text=texto_header, reply_markup=reply_markup, parse_mode='HTML')
    except BadRequest as e:
        # Si el mensaje es una foto (no tiene texto), eliminar primero
        if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
            try:
                await query.message.delete()
            except:
                pass
            # Luego enviar nuevo mensaje con texto y botones
            await context.bot.send_message(chat_id, text=texto_header, reply_markup=reply_markup, parse_mode='HTML')
        elif "Message is not modified" not in str(e):
            logger.warning(f"No se pudo editar el mensaje a galeria_menu: {e}. Enviando uno nuevo.")
            await context.bot.send_message(chat_id, text=texto_header, reply_markup=reply_markup, parse_mode='HTML')

async def show_galeria_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Muestra el contenido detallado de un ítem de la galería, siguiendo la lógica
    de "editar primero" para una transición sin parpadeos.
    """
    query = update.callback_query; await query.answer()
    chat_id = update.effective_chat.id
    item_id = int(query.data.split('_')[-1])

    item_details = await content_db.get_item_details_with_media(item_id, 'gallery', 'title', 'content')

    if not item_details:
        await query.answer("Contenido no disponible.", show_alert=True); return

    context.user_data['gallery_extra_message_ids'] = []
    
    # 1. EDITAR PRIMERO (Lógica de "Ir hacia un ítem")
    # Editamos el mensaje del menú para mostrar el primer trozo de contenido (el texto largo).
    # Esto evita la pantalla en blanco.
    texto_largo = item_details.get('content', 'Cargando contenido...')
    try:
        # Editamos el mensaje del menú para que contenga el texto del ítem
        await query.message.edit_text(text=texto_largo, parse_mode='HTML')
        # Guardamos el ID de este mensaje editado para borrarlo al volver
        context.user_data['gallery_extra_message_ids'].append(query.message.message_id)
    except Exception as e:
        logger.error(f"Error al editar el mensaje inicial en show_galeria_content: {e}")
        # Si la edición falla, lo enviamos como un mensaje nuevo
        msg = await context.bot.send_message(chat_id, text=texto_largo, parse_mode='HTML')
        context.user_data['gallery_extra_message_ids'].append(msg.message_id)


    # 2. ENVIAR MENSAJES ADICIONALES
    media_file_id = item_details.get('media_file_id')
    media_type = item_details.get('media_type')

    if media_file_id:
        try:
            sender_func = context.bot.send_photo if media_type == 'photo' else context.bot.send_video
            media_msg = await sender_func(chat_id=chat_id, **{media_type: media_file_id})
            # Guardamos el ID del mensaje de la imagen/video para borrarlo al volver
            context.user_data['gallery_extra_message_ids'].append(media_msg.message_id)
        except Exception as e:
            logger.error(f"Error al enviar media de la galería: {e}")

    # 3. ENVIAR EL MENSAJE FINAL CON LOS BOTONES DE NAVEGACIÓN
    texto_botones = "👇 Selecciona una opción:"
    reply_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Volver a Galería", callback_data='galeria_menu'),
            InlineKeyboardButton("🏠 Menú Principal", callback_data='main_menu')
        ]
    ])
    await context.bot.send_message(chat_id=chat_id, text=texto_botones, reply_markup=reply_markup)