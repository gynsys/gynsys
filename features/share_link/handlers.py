# features/share_link/handlers.py
import html
from telegram import Update
from telegram.ext import ContextTypes

from features.contacto.user_handler import build_share_code, build_deeplink
from .keyboards import get_share_link_keyboard, get_doctor_share_link_keyboard


async def show_patient_share_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    doctor_id: int,
    doctor_name: str,
):
    """Displays share link info for patients with a return button."""
    query = update.callback_query
    share_code = build_share_code(doctor_id)
    bot_username = getattr(context.bot, "username", None)
    deeplink = build_deeplink(bot_username, doctor_id)

    share_text = (
        "🔗 <b>Comparte el bot de tu médico</b>\n\n"
        f"👩‍⚕️ {html.escape(doctor_name)}\n\n"
        "Copia y comparte este código o enlace con quien necesite agendar "
        "citas y recibir información personalizada:\n\n"
        f"📛 <b>Código:</b>\n<code>{share_code}</code>\n\n"
        f"🌐 <b>Enlace directo:</b>\n{deeplink}"
    )

    if query:
        await query.edit_message_text(
            text=share_text,
            reply_markup=get_share_link_keyboard(),
            parse_mode="HTML",
        )
    else:
        await update.effective_message.reply_text(
            text=share_text,
            reply_markup=get_share_link_keyboard(),
            parse_mode="HTML",
        )


async def show_doctor_share_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    doctor_id: int,
    doctor_name: str,
):
    """Displays share link info for doctors with a return button."""
    query = update.callback_query
    share_code = build_share_code(doctor_id)
    bot_username = getattr(context.bot, "username", None)
    deeplink = build_deeplink(bot_username, doctor_id)

    share_text = (
        "🔗 <b>Comparte tu Bot con tus pacientes</b>\n\n"
        f"👩‍⚕️ {html.escape(doctor_name)}\n\n"
        f"📛 <b>Código para compartir:</b>\n<code>{share_code}</code>\n\n"
        f"🌐 <b>Enlace directo:</b>\n{deeplink}\n\n"
        "Copia y pega este texto en tus mensajes, redes o WhatsApp."
    )

    if query:
        await query.edit_message_text(
            text=share_text,
            reply_markup=get_doctor_share_link_keyboard(),
            parse_mode="HTML",
        )
    else:
        await update.effective_message.reply_text(
            text=share_text,
            reply_markup=get_doctor_share_link_keyboard(),
            parse_mode="HTML",
        )

