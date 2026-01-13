import os
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from config import DB_PATH
from utils.role_manager import RoleManager
from .keyboards import get_marketing_keyboard

role_manager = RoleManager(DB_PATH)

# Ruta al logo de GynSys
LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'utils', 'gyn.png')


MARKETING_TEXT = (
    "🤖 <b>Bienvenido a GynSysBot</b>\n\n"
    "Tu aliado virtual para automatizar tu ejercicio profesional en ginecología y obstetricia.\n"
    "Explora nuestra galería, conoce el plan actual disponible. y descubre cómo podemos ayudarte.\n"
    "Cuando estés listo, solicita tu propio bot con el botón.\n"
    "🤖 Quiero mi Bot."
)

GALLERY_TEXT = (
    "🖼️ <b>Galería</b>\n\n"
    "Mira algunos ejemplos de perfiles públicos, tableros modernos y estadísticas "
    "que los médicos obtienen con GynSys. Próximamente añadiremos imágenes reales."
)

PRICING_TEXT = (
    "💰 <b>Planes</b>\n\n"
    "• Plan Básico: Ideal para comenzar, incluye perfil público y agenda digital.\n"
    "• Plan Profesional: Añade recordatorios automatizados y reportes avanzados.\n"
    "• Plan Clínica: Multiusuario con soporte prioritario y métricas extendidas.\n\n"
    "Contáctanos para recibir la tabla completa de tarifas."
)

ABOUT_TEXT = (
    "ℹ️ <b>Sobre GynSys</b>\n\n"
    "Somos un SaaS especializado en ginecología. Brindamos a cada especialista un "
    "bot personalizado para captar pacientes, gestionar citas y ofrecer experiencias digitales seguras."
)


async def send_marketing_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, *, is_superadmin=False, is_doctor=False):
    keyboard = get_marketing_keyboard(is_superadmin=is_superadmin, is_doctor=is_doctor)

    # Enviar imagen con caption
    message = getattr(update, 'message', None)
    if message:
        with open(LOGO_PATH, 'rb') as photo:
            await message.reply_photo(
                photo=photo,
                caption=MARKETING_TEXT,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
    elif update.callback_query:
        query = update.callback_query
        # Transición fluida: Paso 1 - Editar a texto primero (si es posible)
        # Paso 2 - Luego cambiar a imagen
        try:
            # Paso 1: Intentar editar primero el texto y botones (si es texto)
            await query.edit_message_text(
                text=MARKETING_TEXT,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            # Paso 2: Si fue texto, ahora cambiar a imagen
            with open(LOGO_PATH, 'rb') as photo_file:
                media = InputMediaPhoto(media=photo_file, caption=MARKETING_TEXT, parse_mode="HTML")
                await query.edit_message_media(
                    media=media,
                    reply_markup=keyboard,
                )
        except BadRequest as e:
            # Si el mensaje es una imagen, intentar editar directamente
            if "no text" in str(e).lower():
                try:
                    # Es una imagen, editar caption y botones
                    with open(LOGO_PATH, 'rb') as photo_file:
                        media = InputMediaPhoto(media=photo_file, caption=MARKETING_TEXT, parse_mode="HTML")
                        await query.edit_message_media(
                            media=media,
                            reply_markup=keyboard,
                        )
                except (BadRequest, TypeError):
                    # Si falla, eliminar y enviar nueva
                    try:
                        await query.message.delete()
                    except:
                        pass
                    with open(LOGO_PATH, 'rb') as photo:
                        await context.bot.send_photo(
                            chat_id=query.message.chat.id,
                            photo=photo,
                            caption=MARKETING_TEXT,
                            reply_markup=keyboard,
                            parse_mode="HTML",
                        )
            else:
                # Otro error, eliminar y enviar nueva
                try:
                    await query.message.delete()
                except:
                    pass
                with open(LOGO_PATH, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=query.message.chat.id,
                        photo=photo,
                        caption=MARKETING_TEXT,
                        reply_markup=keyboard,
                        parse_mode="HTML",
                    )


async def handle_marketing_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # await query.answer() # Eliminado para manejarlo individualmente
    user_role = await role_manager.get_user_role(update.effective_user.id)
    keyboard = get_marketing_keyboard(
        is_superadmin=user_role == "superadmin",
        is_doctor=user_role == "doctor",
    )

    data = query.data
    if data == "marketing_gallery":
        await query.answer()
        text = GALLERY_TEXT
        # Para otros callbacks, mostrar texto normal
        try:
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
        except BadRequest:
            # Si falla (ej. es imagen), borrar y enviar nuevo
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    elif data == "marketing_pricing":
        await query.answer(
            text="El costo de lanzamiento de GynSys sera de 3$ mensuales.",
            show_alert=True
        )
        return
    elif data == "marketing_about":
        # El texto es demasiado largo para un alert (max 200 chars). Lo acortamos.
        await query.answer(
            text="SaaS especializado en ginecología. Brindamos a cada especialista un bot personalizado para gestionar citas y ofrecer experiencias digitales seguras.",
            show_alert=True

        )
        return
    else:
        await query.answer()
        # Volver al menú principal (mostrar imagen con caption)
        # Transición fluida: Paso 1 - Editar botones primero, Paso 2 - Luego renderizar imagen
        try:
            # Paso 1: Editar primero a texto con los botones (transición fluida)
            await query.edit_message_text(
                text=MARKETING_TEXT,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            # Paso 2: Luego cambiar a imagen
            with open(LOGO_PATH, 'rb') as photo_file:
                media = InputMediaPhoto(media=photo_file, caption=MARKETING_TEXT, parse_mode="HTML")
                await query.edit_message_media(
                    media=media,
                    reply_markup=keyboard,
                )
        except BadRequest as e:
            # Si ya es imagen, editar directamente
            if "no text" in str(e).lower():
                try:
                    with open(LOGO_PATH, 'rb') as photo_file:
                        media = InputMediaPhoto(media=photo_file, caption=MARKETING_TEXT, parse_mode="HTML")
                        await query.edit_message_media(
                            media=media,
                            reply_markup=keyboard,
                        )
                except (BadRequest, TypeError):
                    # Si falla, eliminar y enviar nuevo
                    try:
                        await query.message.delete()
                    except:
                        pass
                    with open(LOGO_PATH, 'rb') as photo:
                        await context.bot.send_photo(
                            chat_id=query.message.chat.id,
                            photo=photo,
                            caption=MARKETING_TEXT,
                            reply_markup=keyboard,
                            parse_mode="HTML",
                        )
            else:
                # Otro error, eliminar y enviar nuevo
                try:
                    await query.message.delete()
                except:
                    pass
                with open(LOGO_PATH, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=query.message.chat.id,
                        photo=photo,
                        caption=MARKETING_TEXT,
                        reply_markup=keyboard,
                        parse_mode="HTML",
                    )


