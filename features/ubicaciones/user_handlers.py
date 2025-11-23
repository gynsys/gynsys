# features/ubicaciones/user_handlers.py
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes

from config import DB_PATH
from utils.role_manager import RoleManager
from database import locations_db, connection
from common import texts
from common.helpers import escape_html
from .keyboards import get_ubicaciones_keyboard, get_location_detail_keyboard

role_manager = RoleManager(DB_PATH)
LOC_CONTEXT_KEY = "locations_context"


async def _doctor_id_to_bot_id(doctor_id: int) -> int | None:
    """Convierte doctor_id a bot_id (tenant_id)."""
    conn = await connection.get_db_connection()
    bot_id = None
    if conn:
        try:
            # Obtener telegram_id del doctor
            async with conn.execute("SELECT telegram_id FROM doctors WHERE id = ?", (doctor_id,)) as cursor:
                doctor_row = await cursor.fetchone()
                if doctor_row:
                    telegram_id = doctor_row['telegram_id']
                    # Obtener bot_id desde bots usando admin_user_id
                    async with conn.execute("SELECT id FROM bots WHERE admin_user_id = ? AND is_active = 1", (telegram_id,)) as bot_cursor:
                        bot_row = await bot_cursor.fetchone()
                        if bot_row:
                            bot_id = bot_row['id']
        finally:
            await conn.close()
    return bot_id


def _store_locations_context(context: ContextTypes.DEFAULT_TYPE, *, doctor_id: int, list_cb: str, home_cb: str):
    context.user_data[LOC_CONTEXT_KEY] = {
        "doctor_id": doctor_id,
        "list_callback": list_cb,
        "home_callback": home_cb,
    }


def _get_locations_context(context: ContextTypes.DEFAULT_TYPE):
    return context.user_data.get(LOC_CONTEXT_KEY)


def _get_doctor_id_from_context(context: ContextTypes.DEFAULT_TYPE):
    doctor_id = context.user_data.get("patient_doctor_id")
    if doctor_id:
        return doctor_id
    doctor_id = context.user_data.get("locations_doctor_id_override")
    if doctor_id:
        return doctor_id
    return None


async def _resolve_doctor_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    """Resuelve el doctor_id para el usuario actual."""
    from_context = _get_doctor_id_from_context(context)
    if from_context:
        return from_context

    user_id = update.effective_user.id
    doctor = await role_manager.get_doctor_by_telegram_id(user_id)
    if doctor:
        return doctor[0]

    assigned = await role_manager.get_assigned_doctor(user_id)
    if assigned:
        return assigned[0]

    return 1  # SuperAdmin como fallback


async def _render_locations_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    doctor_id: int,
    list_callback: str,
    home_callback: str,
    default_header: str = "📍 Nuestras Ubicaciones",
) -> None:
    # Convertir doctor_id a bot_id para obtener las ubicaciones
    bot_id = await _doctor_id_to_bot_id(doctor_id)
    if not bot_id:
        # Si no se encuentra bot_id, usar doctor_id como fallback (para compatibilidad)
        bot_id = doctor_id
    
    texto = await texts.get_texto("header_sedes", bot_id, default_header)
    reply_markup = await get_ubicaciones_keyboard(bot_id, home_callback)
    _store_locations_context(context, doctor_id=doctor_id, list_cb=list_callback, home_cb=home_callback)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=texto,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    else:
        await update.effective_message.reply_text(
            text=texto,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )


async def show_ubicaciones_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler genérico (marketing/superadmin) para ver ubicaciones."""
    query = update.callback_query
    await query.answer()

    doctor_id = await _resolve_doctor_id(update, context)
    if not doctor_id:
        await query.edit_message_text("❌ No se pudo determinar el perfil del médico.")
        return

    await _render_locations_menu(update, context, doctor_id, list_callback="ubicaciones_menu", home_callback="main_menu")


async def show_patient_locations_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    doctor_id: int,
) -> None:
    """Vista de ubicaciones para pacientes (desde su menú principal)."""
    await _render_locations_menu(
        update,
        context,
        doctor_id,
        list_callback="patient_locations",
        home_callback="patient_main_menu",
    )


async def show_doctor_locations_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Vista de ubicaciones para el médico (desde su menú público)."""
    query = update.callback_query
    await query.answer()

    doctor = await role_manager.get_doctor_by_telegram_id(update.effective_user.id)
    if not doctor:
        await query.edit_message_text(
            "❌ No pudimos identificar tu perfil de médico para mostrar las ubicaciones.",
            parse_mode="HTML",
        )
        return

    await _render_locations_menu(
        update,
        context,
        doctor_id=doctor[0],
        list_callback="doctor_locations",
        home_callback="doctor_main_menu",
    )


async def show_ubicacion_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra los detalles de una ubicación específica."""
    query = update.callback_query
    await query.answer()
    loc_id = int(query.data.split('_')[-1])

    ctx = _get_locations_context(context)
    if not ctx:
        await query.answer("⚠️ Abre las ubicaciones desde el menú antes de ver los detalles.", show_alert=True)
        return

    # Convertir doctor_id a bot_id para verificar la pertenencia
    bot_id = await _doctor_id_to_bot_id(ctx["doctor_id"])
    if not bot_id:
        bot_id = ctx["doctor_id"]  # Fallback

    loc = await locations_db.get_location_details(loc_id)
    if not loc or loc.get("bot_id") != bot_id:
        await query.edit_message_text(
            "❌ Ubicación no encontrada.",
            reply_markup=get_location_detail_keyboard(ctx["list_callback"], ctx["home_callback"]),
        )
        return

    maps_url = loc.get("Maps_url")
    texto = (
        f"🏢 <b>{escape_html(loc['name'])}</b>\n\n"
        f"{escape_html(loc['address'])}\n\n"
        f"<b>Horario:</b> {escape_html(loc['schedule'])}\n\n"
    )
    if maps_url:
        texto += f"<a href='{escape_html(maps_url)}'>Ver en Google Maps</a>"

    await query.edit_message_text(
        text=texto,
        reply_markup=get_location_detail_keyboard(ctx["list_callback"], ctx["home_callback"]),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


def register(app: Application):
    """Registra los handlers del módulo."""
    app.add_handler(CallbackQueryHandler(show_ubicaciones_menu, pattern="^ubicaciones_menu$"))
    app.add_handler(CallbackQueryHandler(show_ubicacion_details, pattern="^sede_select_"))