import re
import logging
from typing import Tuple, Optional
import html

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from config import DB_PATH
from database.session import get_session
from database.repositories.contact_repository import ContactRepository
from utils.role_manager import RoleManager
from .keyboards import (
    get_contact_menu_keyboard,
    get_cancel_edit_keyboard,
    get_back_to_contact_menu_keyboard,
    get_doctor_contact_keyboard,
)

role_manager = RoleManager(DB_PATH)
logger = logging.getLogger("ContactHandler")

(CONTACT_WAITING_VALUE,) = range(1)


FIELD_PROMPTS = {
    "phone": "Ingresa tu número telefónico profesional (incluye prefijo internacional).",
    "whatsapp": "Ingresa tu número o link directo de WhatsApp.",
    "email": "Ingresa tu correo de contacto.",
    "address": "Ingresa la dirección de tu consultorio.",
    "website": "Ingresa el enlace de tu sitio web o perfil.",
}


def validate_field(field: str, value: str) -> Tuple[bool, Optional[str]]:
    value = value.strip()
    if not value:
        return False, "El valor no puede estar vacío."

    if field == "phone":
        if not re.fullmatch(r"[+\d][\d\s\-()]{6,20}", value):
            return False, "Formato de teléfono inválido. Usa solo números y símbolos + - ()."
    elif field == "whatsapp":
        if not re.fullmatch(r"(https://wa\.me/\d+|[+\d][\d\s\-()]{6,20})", value):
            return False, "Ingresa un número válido o un enlace https://wa.me/."
    elif field == "email":
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            return False, "Correo electrónico inválido."
    elif field == "website":
        if not re.match(r"https?://", value):
            return False, "El sitio web debe iniciar con http:// o https://"
    return True, None


async def show_contact_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doctor = await role_manager.get_doctor_by_telegram_id(update.effective_user.id)
    logger.info("show_contact_menu start user_id=%s", getattr(update.effective_user, "id", None))
    if not doctor:
        await _reply(
            update,
            "⚠️ Este módulo solo está disponible para médicos activos.",
            reply_markup=None,
        )
        return

    # Construye interfaz con encabezado + línea actual y una instrucción clara.
    doctor_id, doctor_name = doctor[0], doctor[1]
    async with get_session() as session:
        contact_repo = ContactRepository(session)
        contact = await contact_repo.get_contact(doctor_id) or {}
        wa_raw = (contact.get("whatsapp") or "").strip()
        if not wa_raw:
            wa_line = "Puedes contactarme via Whatsapp a traves de este enlace http://wa.me/580000000000"
        else:
            if wa_raw.startswith("http://") or wa_raw.startswith("https://"):
                wa_link = wa_raw
            else:
                digits = "".join(ch for ch in wa_raw if ch.isdigit())
                wa_link = f"http://wa.me/{digits}" if digits else wa_raw
            wa_line = f"Puedes contactarme via Whatsapp a traves de este enlace {html.escape(wa_link)}"

    text = (
        "📞 <b>Contacto Profesional</b>\n"
        f"👩‍⚕️ {html.escape(doctor_name)}\n\n"
        f"{wa_line}\n\n"
        "✏️ <b>Para actualizar</b>: envía aquí el <b>nuevo link</b> o <b>número</b> de WhatsApp.\n"
        "Ejemplos: https://wa.me/584123456789  |  +58 412 345 6789"
    )

    # Dejar preparado el estado de conversación y recordar el mensaje a editar
    if update.callback_query:
        logger.info("show_contact_menu -> waiting for value via callback, setting state CONTACT_WAITING_VALUE")
        context.user_data["contact_edit_field"] = "whatsapp"
        context.user_data["contact_edit_message"] = (update.callback_query.message.chat_id, update.callback_query.message.message_id)
        await update.callback_query.edit_message_text(
            text,
            reply_markup=get_contact_menu_keyboard(),  # solo 🏠 Inicio
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    else:
        logger.info("show_contact_menu -> waiting for value via message, setting state CONTACT_WAITING_VALUE")
        context.user_data["contact_edit_field"] = "whatsapp"
        context.user_data["contact_edit_message"] = (update.effective_chat.id, None)
        await update.message.reply_text(
            text,
            reply_markup=get_contact_menu_keyboard(),  # solo 🏠 Inicio
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    return CONTACT_WAITING_VALUE


def build_share_code(doctor_id: int) -> str:
    return f"gynsysbot{doctor_id:06d}"


def build_deeplink(username: str, doctor_id: int) -> str:
    if not username:
        return f"https://t.me/<tu_bot>?start=medico_{doctor_id}"
    return f"https://t.me/{username}?start=medico_{doctor_id}"


def build_contact_summary(contact: dict, doctor_name: str, doctor_id: int, bot_username: Optional[str]) -> str:
    def format_value(key, label):
        value = contact.get(key)
        return (
            f"<b>{label}</b>: {html.escape(value)}"
            if value
            else f"<b>{label}</b>: — Sin configurar —"
        )

    share_code = build_share_code(doctor_id)
    deeplink = build_deeplink(bot_username, doctor_id)

    return (
        f"📞 <b>Contacto Profesional</b>\n"
        f"👩‍⚕️ {html.escape(doctor_name)}\n\n"
        f"{format_value('phone', '📞 Teléfono')}\n"
        f"{format_value('whatsapp', '💬 WhatsApp')}\n"
        f"{format_value('email', '✉️ Email')}\n"
        f"{format_value('address', '📍 Dirección')}\n"
        f"{format_value('website', '🌐 Web')}\n\n"
        f"🔗 <b>Comparte este código con tus pacientes:</b>\n"
        f"<code>{share_code}</code>\n"
        f"o envíales tu enlace directo:\n"
        f"{html.escape(deeplink)}"
    )


async def start_contact_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    field = query.data.replace("contact_edit_", "")
    context.user_data["contact_edit_field"] = field
    context.user_data["contact_edit_message"] = (query.message.chat_id, query.message.message_id)
    doctor = await role_manager.get_doctor_by_telegram_id(update.effective_user.id)
    if not doctor:
        await query.edit_message_text(
            "⚠️ Solo los médicos activos pueden editar la información de contacto.",
            parse_mode="HTML",
        )
        return ConversationHandler.END

    prompt = FIELD_PROMPTS.get(field, "Ingresa el nuevo valor.")
    await query.edit_message_text(
        f"✏️ <b>Actualiza tu {html.escape(field.capitalize())}</b>\n\n"
        f"{html.escape(prompt)}\n\nEnvía el nuevo valor:",
        reply_markup=get_cancel_edit_keyboard(),
        parse_mode="HTML",
    )
    return CONTACT_WAITING_VALUE


async def receive_contact_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doctor = await role_manager.get_doctor_by_telegram_id(update.effective_user.id)
    logger.info("receive_contact_value user_id=%s", getattr(update.effective_user, "id", None))
    if not doctor:
        return ConversationHandler.END

    field = context.user_data.get("contact_edit_field")
    message_ref = context.user_data.get("contact_edit_message")

    if not field or not message_ref:
        logger.warning("receive_contact_value: missing state. field=%s message_ref=%s", field, message_ref)
        return ConversationHandler.END

    value = (update.message.text or "").strip()
    logger.info("receive_contact_value: field=%s value='%s' message_ref=%s", field, value, message_ref)

    # Asegurar que el campo sea válido; por defecto forzamos a 'whatsapp'
    allowed_fields = {"phone", "whatsapp", "email", "address", "website"}
    if field not in allowed_fields:
        logger.warning("receive_contact_value: invalid field '%s', coercing to 'whatsapp'", field)
        field = "whatsapp"
        context.user_data["contact_edit_field"] = field
    # Sin validación para WhatsApp según requerimiento
    try:
        await update.message.delete()
    except Exception:
        logger.debug("receive_contact_value: cannot delete user message (ignored)")

    async with get_session() as session:
        contact_repo = ContactRepository(session)
        await contact_repo.update_field(doctor[0], field, value)
    logger.info("receive_contact_value: contact updated doctor_id=%s", doctor[0])

    if field == "whatsapp":
        # Confirmar y luego reemplazar el mismo mensaje por el Menú Principal (pantalla limpia)
        if message_ref[1] is not None:
            try:
                await context.bot.edit_message_text(
                    chat_id=message_ref[0],
                    message_id=message_ref[1],
                    text="✅ <b>WhatsApp actualizado</b>",
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )
            except Exception:
                logger.exception("receive_contact_value: edit confirmation failed, sending new message")
                await context.bot.send_message(
                    chat_id=message_ref[0],
                    text="✅ <b>WhatsApp actualizado</b>",
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )
            # Reemplazar por el menú principal en el mismo mensaje
            from features.main_menu.user_handler import get_doctor_public_keyboard
            import asyncio as _aio
            logger.info("receive_contact_value: switching message to main menu")
            await _aio.sleep(0.3)
            await context.bot.edit_message_text(
                chat_id=message_ref[0],
                message_id=message_ref[1],
                #text=f"👩‍⚕️ <b>Menú Principal - {html.escape(doctor[1])}</b>\n"
                 #    "Comparte estos accesos con tus pacientes y personalízalos desde Panel Admin.",
                reply_markup=get_doctor_public_keyboard(),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        else:
            # No tenemos message_id para editar; enviamos confirmación y luego el menú
            logger.info("receive_contact_value: no message_id, sending confirmation and main menu as new messages")
            await context.bot.send_message(
                chat_id=message_ref[0],
                text="✅ <b>WhatsApp actualizado</b>",
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            from features.main_menu.user_handler import admin_main_menu
            await admin_main_menu(update, context)
    else:
        async with get_session() as session:
            contact_repo = ContactRepository(session)
            contact = await contact_repo.get_contact(doctor[0]) or {}
            summary = build_contact_summary(contact, doctor[1], doctor[0], context.bot.username)
        await context.bot.edit_message_text(
            chat_id=message_ref[0],
            message_id=message_ref[1],
            text=f"✅ <b>{html.escape(field.capitalize())} actualizado</b>\n\n{summary}",
            parse_mode="HTML",
        )

    context.user_data.pop("contact_edit_field", None)
    context.user_data.pop("contact_edit_message", None)
    return ConversationHandler.END


async def show_doctor_contact_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra solo el enlace de WhatsApp del propio doctor con botón Inicio."""
    doc = await role_manager.get_doctor_by_telegram_id(update.effective_user.id)
    if not doc:
        await _reply(update, "⚠️ Solo los médicos activos pueden ver esta sección.")
        return

    doctor_id, doctor_name = doc[0], doc[1]
    async with get_session() as session:
        contact_repo = ContactRepository(session)
        contact = await contact_repo.get_contact(doctor_id) or {}
    wa_raw = (contact.get("whatsapp") or "").strip()
    if not wa_raw:
        text = "Puedes contactarme via Whatsapp a traves de este enlace http://wa.me/580000000000"
    else:
        if wa_raw.startswith("http://") or wa_raw.startswith("https://"):
            wa_link = wa_raw
        else:
            digits = "".join(ch for ch in wa_raw if ch.isdigit())
            wa_link = f"http://wa.me/{digits}" if digits else wa_raw
        text = f"Puedes contactarme via Whatsapp a traves de este enlace {html.escape(wa_link)}"

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=get_doctor_contact_keyboard(),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=get_doctor_contact_keyboard(),
            parse_mode="HTML",
        )

async def cancel_contact_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    doctor = await role_manager.get_doctor_by_telegram_id(query.from_user.id)
    if not doctor:
        await query.edit_message_text(
            "⚠️ Solo los médicos activos pueden editar la información de contacto.",
            parse_mode="HTML",
        )
        return ConversationHandler.END

    async with get_session() as session:
        contact_repo = ContactRepository(session)
        contact = await contact_repo.get_contact(doctor[0]) or {}
        summary = build_contact_summary(contact, doctor[1], doctor[0], context.bot.username)

    await query.edit_message_text(
        summary,
        reply_markup=get_contact_menu_keyboard(),
        parse_mode="HTML",
    )

    context.user_data.pop("contact_edit_field", None)
    context.user_data.pop("contact_edit_message", None)
    return ConversationHandler.END


async def show_contact_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    doctor = await role_manager.get_doctor_by_telegram_id(query.from_user.id)
    if not doctor:
        await query.edit_message_text(
            "⚠️ Solo los médicos activos pueden ver esta información.",
            parse_mode="HTML",
        )
        return

    async with get_session() as session:
        contact_repo = ContactRepository(session)
        contact = await contact_repo.get_contact(doctor[0])
        if not contact:
            await query.edit_message_text(
                "👀 <b>Vista Paciente</b>\n\nAún no has configurado tu información de contacto.",
                reply_markup=get_back_to_contact_menu_keyboard(),
                parse_mode="HTML",
            )
            return

        await query.edit_message_text(
            build_contact_summary(contact, doctor[1], doctor[0], context.bot.username),
            reply_markup=get_back_to_contact_menu_keyboard(),
            parse_mode="HTML",
        )


async def _reply(update: Update, text: str, reply_markup=None):
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )

