from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest
import html

from config import DB_PATH, SUPER_ADMIN_ID
from database.session import get_session
from database.repositories.request_repository import RequestRepository
REQUEST_WAITING_NAME, REQUEST_WAITING_TELEGRAM_ID = range(2)


def get_cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data="request_cancel")]])


def get_success_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Inicio", callback_data="main_menu")]])


async def start_request_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id
    async with get_session() as session:
        repo = RequestRepository(session)
        if await repo.has_pending_request(telegram_id):
            # Manejo específico para cuando el mensaje anterior es una imagen
            try:
                await query.edit_message_text(
                    "⚠️ Ya tienes una solicitud pendiente.\n\nNuestro equipo te notificará cuando sea aprobada.",
                    reply_markup=get_success_keyboard(),
                    parse_mode="HTML",
                )
            except BadRequest as e:
                # Si el mensaje es una foto (no tiene texto), eliminar primero y enviar nuevo
                if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
                    try:
                        await query.message.delete()
                    except:
                        pass
                    await context.bot.send_message(
                        chat_id=query.message.chat.id,
                        text="⚠️ Ya tienes una solicitud pendiente.\n\nNuestro equipo te notificará cuando sea aprobada.",
                        reply_markup=get_success_keyboard(),
                        parse_mode="HTML",
                    )
            return ConversationHandler.END

    context.user_data["doctor_request_message"] = (query.message.chat_id, query.message.message_id)
    # Manejo específico para cuando el mensaje anterior es una imagen
    try:
        await query.edit_message_text(
            "🩺 <b>Solicitud para tu Bot GynSys</b>\n\n"
            "1️⃣ Escribe tu <b>Nombre y Apellido</b>.\n"
            "2️⃣ Luego te pediremos tu <b>ID de Telegram</b>.\n\n"
            "Envía tu nombre ahora:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
    except BadRequest as e:
        # Si el mensaje es una foto (no tiene texto), eliminar primero y enviar nuevo
        if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
            try:
                await query.message.delete()
            except:
                pass
            new_message = await context.bot.send_message(
                chat_id=query.message.chat.id,
                text="🩺 <b>Solicitud para tu Bot GynSys</b>\n\n"
                     "1️⃣ Escribe tu <b>Nombre y Apellido</b>.\n"
                     "2️⃣ Luego te pediremos tu <b>ID de Telegram</b>.\n\n"
                     "Envía tu nombre ahora:",
                reply_markup=get_cancel_keyboard(),
                parse_mode="HTML",
            )
            # Actualizar la referencia del mensaje en user_data
            context.user_data["doctor_request_message"] = (new_message.chat_id, new_message.message_id)
    return REQUEST_WAITING_NAME


async def receive_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_name = update.message.text.strip()
    await update.message.delete()

    context.user_data["doctor_request_name"] = full_name
    message_ref = context.user_data.get("doctor_request_message")

    await context.bot.edit_message_text(
        chat_id=message_ref[0],
        message_id=message_ref[1],
        text=(
            f"✅ Nombre recibido: <b>{html.escape(full_name)}</b>\n\n"
            "Ahora escribe tu <b>ID de Telegram</b> (número que te da @userinfobot)."
        ),
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML",
    )
    return REQUEST_WAITING_TELEGRAM_ID


async def receive_telegram_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id_text = update.message.text.strip()
    await update.message.delete()

    message_ref = context.user_data.get("doctor_request_message")
    full_name = context.user_data.get("doctor_request_name")

    if not telegram_id_text.isdigit():
        await context.bot.edit_message_text(
            chat_id=message_ref[0],
            message_id=message_ref[1],
            text="❌ El ID debe ser numérico. Intenta nuevamente:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML",
        )
        return REQUEST_WAITING_TELEGRAM_ID

    telegram_id = int(telegram_id_text)
    async with get_session() as session:
        repo = RequestRepository(session)
        if await repo.has_pending_request(telegram_id):
            await context.bot.edit_message_text(
                chat_id=message_ref[0],
                message_id=message_ref[1],
                text="⚠️ Este ID ya tiene una solicitud pendiente. Espera la aprobación.",
                reply_markup=get_success_keyboard(),
                parse_mode="HTML",
            )
            return ConversationHandler.END

        request_id = await repo.create_request(full_name, telegram_id, status="pending")

        if request_id:
            try:
                await context.bot.send_message(
                    chat_id=SUPER_ADMIN_ID,
                    text=(
                        "🆕 <b>Nueva solicitud de médico</b>\n\n"
                        f"<b>Nombre:</b> {html.escape(full_name)}\n"
                        f"<b>Telegram ID:</b> {telegram_id}"
                    ),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("✅ Aprobar", callback_data=f"request_approve_{request_id}"),
                                InlineKeyboardButton("❌ Rechazar", callback_data=f"request_reject_{request_id}")
                            ]
                        ]
                    ),
                    parse_mode="HTML",
                )
            except Exception as exc:
                print(f"No se pudo notificar al superadmin: {exc}")

        await context.bot.edit_message_text(
            chat_id=message_ref[0],
            message_id=message_ref[1],
            text=(
                "✅ <b>Solicitud enviada</b>\n\n"
                "Nuestro equipo verificará tus datos y te notificará cuando tu bot esté listo.\n"
                "Gracias por elegir GynSys."
            ),
            reply_markup=get_success_keyboard(),
            parse_mode="HTML",
        )

    context.user_data.pop("doctor_request_name", None)
    context.user_data.pop("doctor_request_message", None)
    return ConversationHandler.END


async def cancel_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    message_ref = context.user_data.get("doctor_request_message")
    if message_ref:
        await context.bot.edit_message_text(
            chat_id=message_ref[0],
            message_id=message_ref[1],
            text="❌ Solicitud cancelada.",
            reply_markup=get_success_keyboard(),
            parse_mode="HTML",
        )

    context.user_data.pop("doctor_request_name", None)
    context.user_data.pop("doctor_request_message", None)
    return ConversationHandler.END

