# utils/context_manager.py
from telegram import Update
from telegram.ext import ContextTypes
from config import SUPER_ADMIN_ID
from database import user_db 

# El bot_id=1 se usará para el contenido del SuperAdmin/Bot Padre.
# Elige otro número si el 1 ya está en uso por un médico real.
SUPERADMIN_TENANT_ID = 1

async def get_tenant_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    user_id = update.effective_user.id

    # Permitir override para que el SuperAdmin pueda gestionar otros tenants
    if context and context.user_data and 'tenant_id_override' in context.user_data:
        return context.user_data['tenant_id_override']

    if user_id == SUPER_ADMIN_ID:
        return SUPERADMIN_TENANT_ID

    tenant_id = await user_db.get_user_tenant(user_id)
    if tenant_id:
        return tenant_id

    # --- ¡CAMBIO AQUÍ! ---
    # Si el usuario no es SuperAdmin ni tiene un tenant asignado (es un usuario público),
    # le mostramos el contenido del bot padre por defecto.
    return SUPERADMIN_TENANT_ID