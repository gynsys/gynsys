import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from database.session import get_session
from database.repositories.user_repository import DoctorRepository, InstitutionUserRepository
from database.models.user import InstitutionUser

logger = logging.getLogger(__name__)

# Estados para ConversationHandler
WAITING_FOR_MEMBER_ID = 1
WAITING_FOR_MEMBER_NAME = 2

async def _is_titular_doctor(telegram_id: int, session) -> bool:
    """Verifica si el usuario es el verdadero dueño del tenant y no un co-usuario."""
    inst_repo = InstitutionUserRepository(session)
    if await inst_repo.get_institution_user(telegram_id):
        return False
    doctor_repo = DoctorRepository(session)
    doctor = await doctor_repo.get_any_doctor_by_telegram_id(telegram_id)
    return bool(doctor)

async def _get_team_menu_keyboard(has_members: bool = False):
    """Genera el teclado para el menú de gestión de equipo"""
    keyboard = [
        [InlineKeyboardButton("➕ Agregar Miembro", callback_data="team_add")],
    ]
    if has_members:
        keyboard.append([
            InlineKeyboardButton("🗑️ Eliminar Miembro", callback_data="team_delete_menu")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Volver a Panel Admin", callback_data="doctor_panel")])
    return InlineKeyboardMarkup(keyboard)

async def team_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menú principal de gestión de equipo (Panel Admin)."""
    if not update.effective_user:
        return

    admin_id = update.effective_user.id
    
    async with get_session() as session:
        if not await _is_titular_doctor(admin_id, session):
            msg = "⛔ Solo el administrador principal de la institución puede gestionar su equipo."
            if update.callback_query:
                await update.callback_query.answer(msg, show_alert=True)
            return

        doctor_repo = DoctorRepository(session)
        titular = await doctor_repo.get_any_doctor_by_telegram_id(admin_id)
        
        if not titular:
            msg = "⛔ No tienes una institución configurada."
            if update.callback_query:
                await update.callback_query.answer(msg, show_alert=True)
            return

        # List members
        from sqlalchemy import select
        result = await session.execute(
            select(InstitutionUser).where(InstitutionUser.institution_id == titular.id)
        )
        members = result.scalars().all()
        has_members = len(members) > 0
        
        text = "👥 **Gestión de Equipo**\n\n"
        if not members:
            text += "Tu equipo está vacío. Puedes agregar colegas que compartirán acceso a esta institución."
        else:
            text += f"Tienes {len(members)} miembros en el equipo:\n\n"
            for m in members:
                text += f"• {m.name} (`{m.telegram_id}`)\n"
                
        keyboard = await _get_team_menu_keyboard(has_members)

        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        else:
            await update.message.reply_text(text, reply_markup=keyboard, parse_mode='Markdown')

async def team_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enruta las acciones directas de botones (sin estado) desde el hub de equipo."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "team_admin_hub":
        await team_hub(update, context)
    elif query.data == "team_delete_menu":
        await show_delete_menu(update, context)
    elif query.data.startswith("team_del_"):
        await delete_member_action(update, context)
    elif query.data == "team_cancel":
        # Finaliza conv de agregar
        await team_hub(update, context)
        return ConversationHandler.END


# ==========================================
# FLUJO ELIMINAR MIEMBRO (Inline, Sin Estado)
# ==========================================

async def show_delete_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra lista de miembros para eliminar."""
    admin_id = update.effective_user.id
    query = update.callback_query
    
    async with get_session() as session:
        doctor_repo = DoctorRepository(session)
        titular = await doctor_repo.get_any_doctor_by_telegram_id(admin_id)
        
        if not titular: return
        
        from sqlalchemy import select
        result = await session.execute(
            select(InstitutionUser).where(InstitutionUser.institution_id == titular.id)
        )
        members = result.scalars().all()
        
        keyboard = []
        for m in members:
            # Inline button format: "team_del_<id>"
            keyboard.append([InlineKeyboardButton(f"❌ {m.name}", callback_data=f"team_del_{m.telegram_id}")])
            
        keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="team_admin_hub")])
        
        await query.edit_message_text(
            "🗑️ **Eliminar Miembro**\nSelecciona el miembro que deseas revocar del acceso a la institución:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

async def delete_member_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta la eliminación del miembro al pulsar el botón."""
    admin_id = update.effective_user.id
    query = update.callback_query
    
    target_id_str = query.data.replace("team_del_", "")
    if not target_id_str.isdigit():
        return
        
    target_id = int(target_id_str)
    
    async with get_session() as session:
        doctor_repo = DoctorRepository(session)
        titular = await doctor_repo.get_any_doctor_by_telegram_id(admin_id)
        
        if not titular: return
        
        inst_repo = InstitutionUserRepository(session)
        member = await inst_repo.get_institution_user(target_id)
        
        if not member or member.institution_id != titular.id:
            await query.answer("⛔ Este usuario ya no pertenece al equipo.", show_alert=True)
            return
            
        name = member.name
        await session.delete(member)
        await session.commit()
        
        await query.answer(f"✅ {name} eliminado del equipo.", show_alert=True)
        # Recargar hub
        await team_hub(update, context)

# ==========================================
# FLUJO AGREGAR MIEMBRO (ConversationHandler)
# ==========================================

async def start_add_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el flujo para agregar a un miembro."""
    query = update.callback_query
    await query.answer()
    
    admin_id = update.effective_user.id
    async with get_session() as session:
        if not await _is_titular_doctor(admin_id, session):
            await query.answer("⛔ Acceso denegado.", show_alert=True)
            return ConversationHandler.END

    keyboard = [[InlineKeyboardButton("🔙 Cancelar", callback_data="team_cancel")]]
    
    await query.edit_message_text(
        "➕ **Agregar Nuevo Miembro**\n\nPor favor, ingresa el **ID de Telegram** del colega que deseas agregar.\n_(Ejemplo: 123456789)_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return WAITING_FOR_MEMBER_ID

async def receive_member_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el ID de telegram y pide el nombre."""
    text = update.message.text.strip()
    
    if not text.isdigit():
        keyboard = [[InlineKeyboardButton("🔙 Cancelar", callback_data="team_cancel")]]
        await update.message.reply_text(
            "⛔ El ID debe contener solo números. Por favor, intenta de nuevo o presiona Cancelar.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return WAITING_FOR_MEMBER_ID
        
    target_id = int(text)
    
    # Validar que no exista ya
    async with get_session() as session:
        inst_repo = InstitutionUserRepository(session)
        existing = await inst_repo.get_institution_user(target_id)
        if existing:
            await update.message.reply_text(f"⛔ El usuario {target_id} ya pertenece a un equipo. Volviendo al panel...")
            await team_hub(update, context)
            return ConversationHandler.END
            
    # Guardar en contexto temporal
    context.user_data['temp_team_member_id'] = target_id
    
    keyboard = [[InlineKeyboardButton("🔙 Cancelar", callback_data="team_cancel")]]
    await update.message.reply_text(
        f"✅ ID ingresado: {target_id}\n\nAhora ingresa el **Nombre** del colega para identificarlo (Ej: Dra. Pérez):",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return WAITING_FOR_MEMBER_NAME

async def receive_member_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el nombre y guarda al miembro."""
    name = update.message.text.strip()
    target_id = context.user_data.get('temp_team_member_id')
    admin_id = update.effective_user.id
    
    if not target_id:
        await update.message.reply_text("Error de sesión. Volviendo al menú...")
        await team_hub(update, context)
        return ConversationHandler.END
        
    async with get_session() as session:
        doctor_repo = DoctorRepository(session)
        titular = await doctor_repo.get_any_doctor_by_telegram_id(admin_id)
        
        if titular:
            new_member = InstitutionUser(
                telegram_id=target_id,
                institution_id=titular.id,
                name=name
            )
            session.add(new_member)
            await session.commit()
            await update.message.reply_text(f"✅ ¡Excelente! **{name}** ha sido agregado(a) a tu equipo con éxito.", parse_mode='Markdown')
        else:
            await update.message.reply_text("⛔ No tienes una institución configurada.")

    # Limpiar
    context.user_data.pop('temp_team_member_id', None)
    
    # Volver al hub
    await team_hub(update, context)
    return ConversationHandler.END

async def cancel_add_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la creación del miembro."""
    query = update.callback_query
    await query.answer()
    context.user_data.pop('temp_team_member_id', None)
    await team_hub(update, context)
    return ConversationHandler.END


def register(application: Application):
    """Registra los handlers de equipo"""
    
    # Manejador conversacional para crear miembros
    team_add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_member, pattern="^team_add$")],
        states={
            WAITING_FOR_MEMBER_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_member_id),
            ],
            WAITING_FOR_MEMBER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_member_name),
            ]
        },
        fallbacks=[CallbackQueryHandler(cancel_add_member, pattern="^team_cancel$")],
        name="team_add_member_conversation",
        persistent=True
    )
    
    application.add_handler(team_add_conv)
