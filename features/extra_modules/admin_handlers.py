"""
Handlers para gestión de módulos extras (SuperAdmin)
"""
import logging
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from database import extra_modules_db
from database.session import get_session
from database.repositories.user_repository import DoctorRepository
from config import DB_PATH
from common.decorators import superadmin_required
from .keyboards import (
    get_extra_modules_hub_keyboard,
    get_doctors_list_keyboard,
    get_doctor_modules_keyboard
)

logger = logging.getLogger(__name__)

@superadmin_required
async def extra_modules_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hub principal de gestión de módulos extras"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "🔧 <b>Gestión de Módulos Extras</b>\n\n"
        "Gestiona funcionalidades adicionales para cada inquilino.\n\n"
        "Selecciona una opción:"
    )
    
    try:
        await query.edit_message_text(
            text,
            reply_markup=get_extra_modules_hub_keyboard(),
            parse_mode="HTML"
        )
    except BadRequest as e:
        if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=text,
                reply_markup=get_extra_modules_hub_keyboard(),
                parse_mode="HTML"
            )

@superadmin_required
async def list_doctors_for_modules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista todos los doctores para gestionar sus módulos"""
    query = update.callback_query
    await query.answer()
    
    # Extraer número de página del callback si existe
    page = 0
    if query.data.startswith("extra_modules_page_"):
        try:
            page = int(query.data.split("_")[-1])
        except (ValueError, IndexError):
            page = 0
    
    doctors = await extra_modules_db.get_all_doctors_with_modules()
    
    if not doctors:
        text = "❌ No hay doctores activos en el sistema."
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Volver", callback_data="extra_modules_hub")]
        ])
    else:
        text = (
            "👨‍⚕️ <b>Selecciona un Doctor</b>\n\n"
            f"Total: {len(doctors)} doctores activos\n\n"
            "Selecciona un doctor para gestionar sus módulos extras:"
        )
        keyboard = get_doctors_list_keyboard(doctors, page=page)
    
    try:
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except BadRequest as e:
        if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
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

@superadmin_required
async def show_doctor_modules(update: Update, context: ContextTypes.DEFAULT_TYPE, doctor_id: int = None):
    """Muestra los módulos disponibles para un doctor específico"""
    query = update.callback_query
    await query.answer()
    
    # Si viene de un callback, extraer el doctor_id
    if doctor_id is None:
        if query.data.startswith("extra_modules_doctor_"):
            try:
                doctor_id = int(query.data.split("_")[-1])
            except (ValueError, IndexError):
                await query.answer("❌ Error: ID de doctor inválido.", show_alert=True)
                return
        else:
            await query.answer("❌ Error: No se especificó el doctor.", show_alert=True)
            return
    
    async with get_session() as session:
        repo = DoctorRepository(session)
        doctor = await repo.get_doctor_by_id(doctor_id)
        if not doctor:
            await query.answer("❌ Doctor no encontrado.", show_alert=True)
            return
        
        doctor_name = doctor.name
        active_modules = await extra_modules_db.get_active_modules_for_doctor(doctor_id)
        available_modules = await extra_modules_db.get_available_modules()
        
        # Construir texto con estado de módulos
        modules_text = "\n".join([
            f"{'✅' if m['name'] in active_modules else '❌'} {m['display_name']}: {m['description']}"
            for m in available_modules
        ])
        
        text = (
            f"🔧 <b>Módulos Extras - {doctor_name}</b>\n\n"
            f"Gestiona las funcionalidades adicionales para este inquilino:\n\n"
            f"{modules_text}\n\n"
            "Presiona un módulo para activarlo/desactivarlo:"
        )
        
        keyboard = get_doctor_modules_keyboard(doctor_id, doctor_name, available_modules, active_modules)
        
        try:
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except BadRequest as e:
            if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
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

@superadmin_required
async def toggle_doctor_module(update: Update, context: ContextTypes.DEFAULT_TYPE, doctor_id: int = None, module_name: str = None):
    """Activa/desactiva un módulo para un doctor"""
    query = update.callback_query
    
    # Si viene de un callback, extraer doctor_id y module_name
    if doctor_id is None or module_name is None:
        if query.data.startswith("extra_modules_toggle_"):
            try:
                parts = query.data.split("_")
                doctor_id = int(parts[3])
                module_name = parts[4]
            except (ValueError, IndexError):
                await query.answer("❌ Error: Datos inválidos.", show_alert=True)
                return
        else:
            await query.answer("❌ Error: No se especificaron los datos.", show_alert=True)
            return
    
    success = await extra_modules_db.toggle_module_for_doctor(doctor_id, module_name)
    
    if success:
        is_active = await extra_modules_db.is_module_active_for_doctor(doctor_id, module_name)
        status = "activado" if is_active else "desactivado"
        await query.answer(f"✅ Módulo {status} correctamente.", show_alert=True)
        
        # Refrescar la vista
        await show_doctor_modules(update, context, doctor_id)
    else:
        await query.answer("❌ Error al cambiar el estado del módulo.", show_alert=True)

def register(app):
    """Registra los handlers de módulos extras"""
    from telegram.ext import CallbackQueryHandler
    
    app.add_handler(CallbackQueryHandler(extra_modules_hub, pattern='^extra_modules_hub$'))
    app.add_handler(CallbackQueryHandler(list_doctors_for_modules, pattern='^extra_modules_by_doctor$'))
    app.add_handler(CallbackQueryHandler(list_doctors_for_modules, pattern='^extra_modules_page_\d+$'))
    app.add_handler(CallbackQueryHandler(show_doctor_modules, pattern='^extra_modules_doctor_\d+$'))
    app.add_handler(CallbackQueryHandler(toggle_doctor_module, pattern='^extra_modules_toggle_\d+_\w+$'))

