import time
import logging
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import SUPER_ADMIN_ID
from utils.role_manager import RoleManager
from config import DB_PATH


# TODO: Adaptar para multi-tenant - temporalmente comentado
# from database import user_db
role_manager = RoleManager(DB_PATH)
logger = logging.getLogger(__name__)

def doctor_required(func):
    """
    Decorador que restringe el acceso solo a usuarios con rol 'doctor'.
    """
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        user_role = await role_manager.get_user_role(user_id)

        if user_role != 'doctor':
            logger.warning(f"Acceso DENEGADO al usuario {user_id} (rol: {user_role}) para la función de doctor: {func.__name__}.")
            if update.callback_query:
                await update.callback_query.answer("🚫 Esta función es solo para médicos.", show_alert=True)
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapped
# --- DECORADOR admin_required ---
def admin_required(func):
    """
    Decorador que restringe el acceso de un handler solo a doctores activos (multi-tenant) y al superadmin.
    """
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        func_name = func.__name__
        
        # Print directo para debugging (siempre se muestra)
        print(f"🔐 [admin_required] Decorador ejecutado para función: {func_name}, User ID: {user_id}")
        logger.info(f"[admin_required] Decorador ejecutado para función: {func_name}, User ID: {user_id}")
        
        # Permitir acceso al superadmin
        if user_id == SUPER_ADMIN_ID:
            print(f"🔐 [admin_required] ✅ Usuario {user_id} es SUPER_ADMIN_ID, permitiendo acceso a {func_name}")
            logger.info(f"[admin_required] ✅ Usuario {user_id} es SUPER_ADMIN_ID, permitiendo acceso a {func_name}")
            try:
                result = await func(update, context, *args, **kwargs)
                print(f"🔐 [admin_required] ✅ Función {func_name} ejecutada exitosamente para superadmin")
                logger.info(f"[admin_required] ✅ Función {func_name} ejecutada exitosamente para superadmin")
                return result
            except Exception as e:
                print(f"🔐 [admin_required] ❌ Error ejecutando {func_name} para superadmin: {e}")
                logger.error(f"[admin_required] ❌ Error ejecutando {func_name} para superadmin: {e}", exc_info=True)
                raise
        
        # Verificar si el usuario es un doctor activo (multi-tenant)
        is_doctor = await role_manager.is_doctor_active(user_id)
        
        if not is_doctor:
            logger.warning(f"[admin_required] Acceso denegado al usuario {user_id} para la función {func_name}. No es un doctor activo.")
            if update.callback_query:
                await update.callback_query.answer("❌ No tienes permiso para realizar esta acción.", show_alert=True)
            elif update.message:
                await update.message.reply_text("🚫 No tienes permiso para usar este comando.")
            return

        logger.info(f"[admin_required] ✅ Usuario {user_id} es doctor activo, permitiendo acceso a {func_name}")
        try:
            result = await func(update, context, *args, **kwargs)
            logger.info(f"[admin_required] ✅ Función {func_name} ejecutada exitosamente para doctor")
            return result
        except Exception as e:
            logger.error(f"[admin_required] ❌ Error ejecutando {func_name} para doctor: {e}", exc_info=True)
            raise
    return wrapped

# --- DECORADOR rate_limit ---
ACTION_COOLDOWNS = {
    'agendar_cita': 86400,  # 24 horas
    'realizar_test': 604800 # 7 días
}

def rate_limit(action_key: str):
    """
    Decorador que previene que un usuario realice una acción clave demasiado rápido,
    ignorando el límite si el usuario es un doctor activo (multi-tenant).
    """
    def decorator(func):
        @wraps(func)
        async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id

            # Verificar si el usuario es un doctor activo (multi-tenant)
            is_doctor = await role_manager.is_doctor_active(user_id)
            if is_doctor:
                return await func(update, context, *args, **kwargs)

            # TODO: Adaptar para multi-tenant - implementar rate limiting por doctor_id
            # Por ahora, permitir todas las acciones (se puede implementar después si es necesario)
            last_timestamp = None  # Temporal
            current_time = int(time.time())
            cooldown = ACTION_COOLDOWNS.get(action_key, 300)

            if last_timestamp and (current_time - last_timestamp) < cooldown:
                message = ""
                keyboard = []
                query = update.callback_query

                if action_key == 'start_endo_test':
                    message = "⏱️ Ya has realizado este test recientemente. Por favor, espera antes de volver a intentarlo."
                    keyboard.append([InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data='main_menu')])

                elif action_key == 'agendar_cita':
                    message = "⏱️ Ya tienes una cita agendada o has agendado una recientemente."
                    keyboard.append([InlineKeyboardButton("🏠 Volver al Menú Principal", callback_data='main_menu')])

                if message and query:
                    await query.answer()
                    await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard))
                return

            # TODO: Adaptar para multi-tenant - log de acciones por doctor_id
            # await user_db.log_user_action(user_id, doctor_id, action_key, current_time)
            pass  # Temporal
            return await func(update, context, *args, **kwargs)
        return wrapped
    return decorator

def superadmin_required(func):
    """
    Decorador que restringe el acceso de un handler solo al SUPER_ADMIN_ID global.
    Es ideal para funciones del panel del bot padre.
    """
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != SUPER_ADMIN_ID:
            logger.warning(f"Acceso DENEGADO al usuario {user_id} para la función de superadmin: {func.__name__}.")
            if update.callback_query:
                await update.callback_query.answer("🚫 Acceso denegado.", show_alert=True)
            return  # Detiene la ejecución
        
        # Si el ID coincide, ejecuta la función original
        return await func(update, context, *args, **kwargs)
    return wrapped