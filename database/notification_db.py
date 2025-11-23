# database/notification_db.py
"""
Capa de compatibilidad para notification_db.py.
Migrado a SQLAlchemy asíncrono usando NotificationRepository.
"""
import asyncio
import logging
from .session import get_session
from .repositories.notification_repository import NotificationRepository

logger = logging.getLogger(__name__)


async def create_notification(bot_id: int, user_id: int, message: str, notification_type: str = 'info') -> int | None:
    """Crea una nueva notificación para un usuario."""
    async with get_session() as session:
        repo = NotificationRepository(session)
        return await repo.create_notification(bot_id, user_id, message, notification_type)


async def get_unread_notification_count(user_id: int, bot_id: int) -> int:
    """Obtiene el número de notificaciones no leídas de un usuario."""
    async with get_session() as session:
        repo = NotificationRepository(session)
        return await repo.get_unread_notification_count(user_id, bot_id)


async def mark_notifications_as_read(user_id: int, bot_id: int) -> bool:
    """Marca todas las notificaciones de un usuario como leídas."""
    async with get_session() as session:
        repo = NotificationRepository(session)
        return await repo.mark_notifications_as_read(user_id, bot_id)


async def get_recent_notifications(user_id: int, bot_id: int, limit: int = 10):
    """Obtiene las notificaciones recientes de un usuario."""
    async with get_session() as session:
        repo = NotificationRepository(session)
        return await repo.get_recent_notifications(user_id, bot_id, limit)