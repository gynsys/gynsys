# database/user_db.py
"""
Capa de compatibilidad para user_db.py.
Migrado a SQLAlchemy asíncrono usando UserUtilRepository.
"""
import asyncio
import logging
from .session import get_session
from .repositories.user_util_repository import (
    BotRepository,
    BotLogoRepository,
    UserActionRepository
)

logger = logging.getLogger(__name__)


async def get_user_tenant(user_id: int) -> int | None:
    """Obtiene el tenant_id (bot_id) al que pertenece un usuario"""
    async with get_session() as session:
        repo = BotRepository(session)
        return await repo.get_user_tenant(user_id)


async def is_user_admin_for_current_context(user_id: int, bot_id: int) -> bool:
    """Verifica si el usuario es admin del tenant actual"""
    return await is_user_admin_for_bot(user_id, bot_id)


async def is_user_an_admin(user_id: int) -> bool:
    """Verifica si el usuario es admin de CUALQUIER tenant (para Super Admin)"""
    async with get_session() as session:
        repo = BotRepository(session)
        return await repo.is_user_an_admin(user_id)


async def is_user_admin_for_bot(user_id: int, bot_id: int) -> bool:
    """Verifica si el usuario es admin del bot específico"""
    async with get_session() as session:
        repo = BotRepository(session)
        return await repo.is_user_admin_for_bot(user_id, bot_id)


async def get_bot_admin_id(bot_id: int) -> int | None:
    """Obtiene el admin_user_id de un bot"""
    async with get_session() as session:
        repo = BotRepository(session)
        return await repo.get_bot_admin_id(bot_id)


async def add_new_bot(doctor_name: str, admin_user_id: int) -> int | None:
    """Crea un nuevo bot"""
    async with get_session() as session:
        repo = BotRepository(session)
        return await repo.add_new_bot(doctor_name, admin_user_id)


async def get_bot_logo_paths(bot_id: int) -> dict | None:
    """Obtiene todas las rutas de logos para un bot específico."""
    async with get_session() as session:
        repo = BotLogoRepository(session)
        return await repo.get_bot_logo_paths(bot_id)


async def update_bot_logo_path(bot_id: int, logo_type: str, file_path: str):
    """
    Guarda o actualiza la ruta de un logo para un bot.
    
    Args:
        bot_id: ID del bot
        logo_type: 'header1', 'header2', o 'signature'
        file_path: Ruta del archivo
    """
    async with get_session() as session:
        repo = BotLogoRepository(session)
        await repo.update_bot_logo_path(bot_id, logo_type, file_path)


async def delete_bot_logo_path(bot_id: int, logo_type: str) -> bool:
    """
    Elimina la ruta de un logo de la BD y borra el archivo físico.
    
    Args:
        bot_id: ID del bot
        logo_type: 'header1', 'header2', o 'signature'
    """
    async with get_session() as session:
        repo = BotLogoRepository(session)
        return await repo.delete_bot_logo_path(bot_id, logo_type)


async def log_user_action(user_id: int, bot_id: int, action_key: str, timestamp: int):
    """Registra una acción de usuario"""
    async with get_session() as session:
        repo = UserActionRepository(session)
        await repo.log_user_action(user_id, bot_id, action_key, timestamp)


async def get_last_action_timestamp(user_id: int, bot_id: int, action_key: str) -> int | None:
    """Obtiene el timestamp de la última vez que un usuario realizó una acción."""
    async with get_session() as session:
        repo = UserActionRepository(session)
        return await repo.get_last_action_timestamp(user_id, bot_id, action_key)


async def has_user_completed_action(user_id: int, bot_id: int, action_key: str) -> bool:
    """Verifica si un usuario ha completado una acción"""
    async with get_session() as session:
        repo = UserActionRepository(session)
        return await repo.has_user_completed_action(user_id, bot_id, action_key)
