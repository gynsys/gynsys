from telegram import Update
from telegram.ext import ContextTypes
import html

from config import DB_PATH
from utils.role_manager import RoleManager
from features.contacto.patient_handler import show_patient_contact
from features.share_link.handlers import show_patient_share_link
from features.ubicaciones.user_handlers import show_patient_locations_menu
from features.patient_menu.patient_keyboards import get_patient_main_keyboard
from common.helpers import cleanup_extra_messages

role_manager = RoleManager(DB_PATH)
 


def _patient_placeholder(section: str, doctor_name: str) -> str:
    return (
        f"{section}\n\n"
        f"Contenido personalizado de {html.escape(doctor_name)} próximamente."
    )


async def patient_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, doctor_id: int):
    # --- INICIO DE LA MODIFICACIÓN ---
    # 1. Limpiamos cualquier mensaje extra antes de hacer nada más.
    await cleanup_extra_messages(context, update.effective_chat.id)
    # --- FIN DE LA MODIFICACIÓN ---

    # El resto de tu lógica original se mantiene intacta.
    context.user_data["patient_doctor_id"] = doctor_id
    doctor = await role_manager.get_doctor_by_id(doctor_id)
    doctor_name = html.escape(doctor[1]) if doctor else "tu doctora"
    
    # Obtener bot_id del doctor para el mensaje de bienvenida
    bot_id = None
    if doctor:
        doctor_telegram_id = doctor[2]  # telegram_id está en índice 2
        import aiosqlite
        from config import DB_PATH
        async with aiosqlite.connect(DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                'SELECT id FROM bots WHERE admin_user_id = ? AND is_active = 1',
                (doctor_telegram_id,)
            )
            result = await cursor.fetchone()
            if result:
                bot_id = result['id']
    
    # Obtener mensaje de bienvenida personalizado
    from common import texts
    user_name = update.effective_user.first_name or "Usuario"
    mensaje_bienvenida = await texts.get_mensaje_bienvenida(nombre_usuario=user_name, bot_id=bot_id if bot_id else 1)
    
    message = (
        f"{mensaje_bienvenida}\n\n"
    )
    
    keyboard = await get_patient_main_keyboard(doctor_id=doctor_id)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    elif update.message:
        await update.message.reply_text(
            message,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    else:
        chat_id = update.effective_chat.id
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

async def handle_patient_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    user_id = update.effective_user.id

    doctor_id = context.user_data.get("patient_doctor_id")
    doctor = None
    if not doctor_id:
        assigned_doctor = await role_manager.get_assigned_doctor(user_id)
        if assigned_doctor:
            doctor_id = assigned_doctor[0]
    if doctor_id:
        doctor = await role_manager.get_doctor_by_id(doctor_id)

    if callback_data == "patient_main_menu":
        if doctor_id:
            await patient_main_menu(update, context, doctor_id)
        else:
            await query.edit_message_text(
                "❌ No tienes un médico asignado actualmente.",
                parse_mode="Markdown",
            )
        return

    if not doctor_id:
        await query.edit_message_text(
            "❌ Aún no tienes un médico asignado.",
            parse_mode="Markdown",
        )
        return

    doctor_name = doctor[1] if doctor else "tu doctora"

    if callback_data == "patient_contact_doctor":
        await show_patient_contact(update, context, doctor_id)
    elif callback_data == "patient_gallery":
        # Llamar al handler real de galería para mostrar el submenú con items
        from features.galeria.user_handlers import show_galeria_menu
        await show_galeria_menu(update, context)
    elif callback_data == "patient_pricing":
        from features.precios.user_handlers import show_precios_menu
        await show_precios_menu(update, context)
        return
    elif callback_data == "patient_share_link":
        await show_patient_share_link(update, context, doctor_id, doctor_name)
    elif callback_data == "patient_locations":
        await show_patient_locations_menu(update, context, doctor_id)
    elif callback_data == "patient_faq":
        from features.faqs.user_handlers import show_faqs_menu
        await show_faqs_menu(update, context)
        return
    elif callback_data == "patient_book_appointment":
        from features.citas.user_handlers import start_booking
        # Guardar doctor_id en context para que start_booking lo encuentre
        context.user_data["patient_doctor_id"] = doctor_id
        await start_booking(update, context)
