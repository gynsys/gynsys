from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest
import html
import logging

from config import (
    DB_PATH, SUPER_ADMIN_ID, PAYPAL_SUBSCRIPTION_COST,
    PAGO_MOVIL_BANK_CODE, PAGO_MOVIL_ID, PAGO_MOVIL_PHONE, PAGO_MOVIL_COST_USD
)
from database.session import get_session
from database.repositories.request_repository import RequestRepository
from utils.paypal_service import PayPalService
from utils.currency_service import get_bcv_rate

logger = logging.getLogger(__name__)

REQUEST_WAITING_PAYMENT, REQUEST_WAITING_REFERENCE, REQUEST_WAITING_NAME, REQUEST_WAITING_TELEGRAM_ID = range(4)


def get_cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data="request_cancel")]])


def get_success_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Inicio", callback_data="main_menu")]])


async def start_request_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # ⚠️ CRÍTICO: Limpiar user_data al inicio para evitar estados residuales
    # Esto previene que el flujo se trabe la primera vez
    context.user_data.pop("doctor_request_name", None)
    context.user_data.pop("doctor_request_message", None)
    
    logger.info(f"start_request_bot: Iniciando solicitud para usuario {update.effective_user.id}")

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

    # Guardar referencia al mensaje después de limpiar user_data
    context.user_data["doctor_request_message"] = (query.message.chat_id, query.message.message_id)
    
    keyboard = [
        [InlineKeyboardButton(f"💳 PayPal (${PAYPAL_SUBSCRIPTION_COST})", callback_data="pay_subscription")],
        [InlineKeyboardButton(f"📱 Pago Móvil (${PAGO_MOVIL_COST_USD})", callback_data="pay_pago_movil")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="request_cancel")]
    ]
    
    text = (
        "💎 <b>Suscripción GynSys</b>\n\n"
        "Selecciona tu método de pago preferido para activar tu bot:\n\n"
        f"• <b>PayPal</b>: ${PAYPAL_SUBSCRIPTION_COST} USD (Automático)\n"
        f"• <b>Pago Móvil</b>: ${PAGO_MOVIL_COST_USD} USD (Tasa BCV)\n"
    )

    # Manejo específico para cuando el mensaje anterior es una imagen
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard),
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
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="HTML",
            )
            # Actualizar la referencia del mensaje en user_data
            context.user_data["doctor_request_message"] = (new_message.chat_id, new_message.message_id)
    return REQUEST_WAITING_PAYMENT


async def handle_pago_movil_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los datos para Pago Móvil"""
    query = update.callback_query
    await query.answer("Consultando tasa BCV...")
    
    # Obtener tasa
    rate = await get_bcv_rate()
    if rate:
        amount_bs = float(PAGO_MOVIL_COST_USD) * rate
        rate_text = f"Bs. {rate:,.2f}"
        amount_text = f"Bs. {amount_bs:,.2f}"
    else:
        # Fallback si falla la API
        rate_text = "Consultar BCV"
        amount_text = f"${PAGO_MOVIL_COST_USD} (al cambio del día)"
    
    text = (
        "📱 <b>Datos Pago Móvil</b>\n\n"
        f"<b>Banco:</b> Venezuela ({PAGO_MOVIL_BANK_CODE})\n"
        f"<b>C.I:</b> {PAGO_MOVIL_ID}\n"
        f"<b>Teléfono:</b> {PAGO_MOVIL_PHONE}\n\n"
        f"<b>Monto:</b> {amount_text}\n"
        f"<b>Tasa:</b> {rate_text}\n\n"
        "⚠️ Realiza el pago y luego presiona el botón de confirmación."
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ Ya he realizado el pago", callback_data="confirm_pago_movil")],
        [InlineKeyboardButton("🔙 Volver", callback_data="start_request_bot_back")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="request_cancel")]
    ]
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return REQUEST_WAITING_PAYMENT


async def confirm_pago_movil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirma el pago móvil (manual) y pide referencia"""
    query = update.callback_query
    await query.answer()
    
    # Marcamos en user_data que fue pago móvil
    context.user_data["payment_method"] = "pago_movil"
    
    await query.edit_message_text(
        "✅ <b>Pago Reportado</b>\n\n"
        "Por favor, ingresa los <b>últimos 4 dígitos</b> de la referencia bancaria para facilitar la verificación.\n\n"
        "Escribe los 4 dígitos ahora:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    return REQUEST_WAITING_REFERENCE


async def receive_pago_movil_reference(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe los 4 dígitos de la referencia"""
    reference = update.message.text.strip()
    
    # Validación simple
    if not reference.isdigit() or len(reference) < 4:
        await update.message.reply_text(
            "⚠️ Por favor ingresa al menos los últimos 4 dígitos numéricos de la referencia.",
            reply_markup=get_cancel_keyboard()
        )
        return REQUEST_WAITING_REFERENCE

    context.user_data["payment_reference"] = reference
    
    await update.message.reply_text(
        f"📝 Referencia recibida: <b>{reference}</b>\n\n"
        "Verificaremos tu transferencia manualmente.\n"
        "Mientras tanto, continuemos con el registro.\n\n"
        "1️⃣ Escribe tu <b>Nombre y Apellido</b>.\n"
        "2️⃣ Luego te pediremos tu <b>ID de Telegram</b>.\n\n"
        "Envía tu nombre ahora:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    return REQUEST_WAITING_NAME


async def handle_payment_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera el enlace de pago de PayPal"""
    query = update.callback_query
    await query.answer("Generando enlace de pago...")
    
    paypal_service = PayPalService()
    order = await paypal_service.create_order(amount=PAYPAL_SUBSCRIPTION_COST)
    
    if not order or "links" not in order:
        await query.edit_message_text(
            "❌ Error al generar el pago. Por favor intenta nuevamente más tarde.",
            reply_markup=get_cancel_keyboard()
        )
        return REQUEST_WAITING_PAYMENT
        
    # Buscar el link de aprobación
    approve_link = next((link["href"] for link in order["links"] if link["rel"] == "approve"), None)
    order_id = order["id"]
    
    if not approve_link:
        await query.edit_message_text(
            "❌ Error: No se recibió enlace de aprobación de PayPal.",
            reply_markup=get_cancel_keyboard()
        )
        return REQUEST_WAITING_PAYMENT
        
    # Guardar order_id en user_data para verificar después
    context.user_data["paypal_order_id"] = order_id
    
    keyboard = [
        [InlineKeyboardButton("🔗 Ir a Pagar en PayPal", url=approve_link)],
        [InlineKeyboardButton("✅ Ya he pagado", callback_data="check_payment")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="request_cancel")]
    ]
    
    await query.edit_message_text(
        f"💳 <b>Orden de Pago Generada</b>\n\n"
        f"1️⃣ Haz clic en el botón para pagar en PayPal.\n"
        f"2️⃣ Completa el pago de <b>${PAYPAL_SUBSCRIPTION_COST} USD</b>.\n"
        f"3️⃣ Regresa aquí y presiona 'Ya he pagado'.\n\n"
        f"ID de Orden: <code>{order_id}</code>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return REQUEST_WAITING_PAYMENT


async def check_payment_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verifica si el pago fue completado"""
    query = update.callback_query
    await query.answer("Verificando pago...")
    
    order_id = context.user_data.get("paypal_order_id")
    if not order_id:
        await query.edit_message_text(
            "❌ No se encontró una orden de pago activa. Por favor inicia de nuevo.",
            reply_markup=get_cancel_keyboard()
        )
        return REQUEST_WAITING_PAYMENT
        
    paypal_service = PayPalService()
    # Intentar capturar la orden (si no ha sido capturada aún)
    result = await paypal_service.capture_order(order_id)
    
    if not result:
        await query.answer("❌ Error al verificar el pago.", show_alert=True)
        return REQUEST_WAITING_PAYMENT
        
    status = result.get("status")
    
    if status == "COMPLETED":
        context.user_data["payment_method"] = "paypal"
        await query.edit_message_text(
            "✅ <b>¡Pago Exitoso!</b>\n\n"
            "Gracias por tu suscripción. Ahora continuemos con el registro.\n\n"
            "1️⃣ Escribe tu <b>Nombre y Apellido</b>.\n"
            "2️⃣ Luego te pediremos tu <b>ID de Telegram</b>.\n\n"
            "Envía tu nombre ahora:",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return REQUEST_WAITING_NAME
    else:
        await query.answer(f"⚠️ El pago aún no está completado. Estado: {status}", show_alert=True)
        return REQUEST_WAITING_PAYMENT


async def receive_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recibe el nombre completo del usuario y solicita el ID de Telegram.
    Esta función es crítica para el flujo de solicitud de bot.
    """
    try:
        # Validar que hay un mensaje de texto
        if not update.message or not update.message.text:
            logger.warning("receive_full_name: No hay mensaje de texto")
            return ConversationHandler.END
        
        full_name = update.message.text.strip()
        
        # Validar que el nombre no esté vacío
        if not full_name:
            await update.message.reply_text(
                "❌ El nombre no puede estar vacío. Por favor, envía tu nombre completo:",
                reply_markup=get_cancel_keyboard(),
                parse_mode="HTML",
            )
            return REQUEST_WAITING_NAME
        
        logger.info(f"receive_full_name: Nombre recibido: {full_name} para usuario {update.effective_user.id}")
        
        # Intentar eliminar el mensaje del usuario (no crítico si falla)
        try:
            await update.message.delete()
        except Exception as e:
            logger.warning(f"receive_full_name: No se pudo eliminar mensaje: {e}")
        
        # Guardar el nombre en user_data
        context.user_data["doctor_request_name"] = full_name
        
        # Obtener referencia al mensaje anterior
        message_ref = context.user_data.get("doctor_request_message")
        
        # Preparar el mensaje de respuesta
        response_text = (
            f"✅ Nombre recibido: <b>{html.escape(full_name)}</b>\n\n"
            "Ahora escribe tu <b>ID de Telegram</b> (número que te da @userinfobot)."
        )
        
        # Intentar editar el mensaje anterior o enviar uno nuevo
        if message_ref:
            try:
                await context.bot.edit_message_text(
                    chat_id=message_ref[0],
                    message_id=message_ref[1],
                    text=response_text,
                    reply_markup=get_cancel_keyboard(),
                    parse_mode="HTML",
                )
                logger.info(f"receive_full_name: Mensaje editado exitosamente. Estado: REQUEST_WAITING_TELEGRAM_ID")
            except Exception as e:
                # Si falla editar, enviar mensaje nuevo
                logger.warning(f"receive_full_name: Error editando mensaje: {e}. Enviando mensaje nuevo.")
                new_message = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=response_text,
                    reply_markup=get_cancel_keyboard(),
                    parse_mode="HTML",
                )
                context.user_data["doctor_request_message"] = (new_message.chat_id, new_message.message_id)
        else:
            # Si no hay referencia, enviar mensaje nuevo
            logger.info("receive_full_name: No hay referencia a mensaje anterior. Enviando mensaje nuevo.")
            new_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=response_text,
                reply_markup=get_cancel_keyboard(),
                parse_mode="HTML",
            )
            context.user_data["doctor_request_message"] = (new_message.chat_id, new_message.message_id)
        
        # CRÍTICO: Retornar el estado siguiente
        logger.info(f"receive_full_name: Retornando REQUEST_WAITING_TELEGRAM_ID ({REQUEST_WAITING_TELEGRAM_ID})")
        return REQUEST_WAITING_TELEGRAM_ID
        
    except Exception as e:
        logger.error(f"Error en receive_full_name: {e}", exc_info=True)
        try:
            await update.message.reply_text(
                "❌ Ocurrió un error. Por favor, intenta nuevamente usando /start",
                parse_mode="HTML",
            )
        except:
            pass
        return ConversationHandler.END


async def receive_telegram_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        telegram_id_text = update.message.text.strip()
        try:
            await update.message.delete()
        except Exception:
            pass

        message_ref = context.user_data.get("doctor_request_message")
        full_name = context.user_data.get("doctor_request_name")

        # Validar datos críticos
        if not message_ref:
            logger.error("receive_telegram_id: message_ref is None")
            await update.message.reply_text("❌ Error de sesión. Por favor inicia de nuevo con /start")
            return ConversationHandler.END
            
        if not full_name:
            logger.error("receive_telegram_id: full_name is None")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Error: Nombre no encontrado. Por favor inicia de nuevo."
            )
            return ConversationHandler.END

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

        # Recuperar datos de pago
        payment_method = context.user_data.get("payment_method", "unknown")
        payment_ref = context.user_data.get("payment_reference", "N/A")
        paypal_order = context.user_data.get("paypal_order_id", "N/A")
        
        payment_info = ""
        if payment_method == "pago_movil":
            payment_info = f"\n<b>Pago Móvil Ref:</b> {html.escape(str(payment_ref))}"
        elif payment_method == "paypal":
            payment_info = f"\n<b>PayPal Order:</b> {html.escape(str(paypal_order))}"

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
                            f"{payment_info}"
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
                    logger.error(f"No se pudo notificar al superadmin: {exc}")

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

    except Exception as e:
        logger.error(f"Error crítico en receive_telegram_id: {e}", exc_info=True)
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="❌ Ocurrió un error inesperado al procesar tu solicitud. Por favor contacta a soporte."
            )
        except:
            pass
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

