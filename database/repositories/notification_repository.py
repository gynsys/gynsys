"""
Repository para gestionar notificaciones.
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from .base_repository import BaseRepository
from database.models.notification import Notification
import logging

logger = logging.getLogger(__name__)


class NotificationRepository(BaseRepository[Notification]):
    """
    Repository para operaciones con notificaciones.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(Notification, session)
    
    async def create_notification(
        self,
        bot_id: int,
        user_id: int,
        message: str,
        notification_type: str = 'info'
    ) -> Optional[int]:
        """
        Crea una nueva notificación para un usuario.
        
        Returns:
            ID de la notificación creada, o None si hay error.
        """
        try:
            notification = Notification(
                bot_id=bot_id,
                user_id=user_id,
                message=message,
                notification_type=notification_type,
                is_read=False
            )
            self.session.add(notification)
            await self.session.flush()
            notification_id = notification.id
            logger.info(f"Notificación creada para usuario {user_id}: {message}")
            return notification_id
        except Exception as e:
            logger.error(f"Error al crear notificación: {e}")
            await self.session.rollback()
            return None
    
    async def get_unread_notification_count(
        self,
        user_id: int,
        bot_id: int
    ) -> int:
        """
        Obtiene el número de notificaciones no leídas de un usuario.
        """
        try:
            stmt = select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.bot_id == bot_id,
                Notification.is_read == False
            )
            result = await self.session.execute(stmt)
            count = result.scalar() or 0
            return count
        except Exception as e:
            logger.error(f"Error al contar notificaciones no leídas: {e}")
            return 0
    
    async def mark_notifications_as_read(
        self,
        user_id: int,
        bot_id: int
    ) -> bool:
        """
        Marca todas las notificaciones de un usuario como leídas.
        """
        try:
            stmt = select(Notification).where(
                Notification.user_id == user_id,
                Notification.bot_id == bot_id,
                Notification.is_read == False
            )
            result = await self.session.execute(stmt)
            notifications = result.scalars().all()
            
            for notification in notifications:
                notification.is_read = True
            
            await self.session.flush()
            logger.info(f"Notificaciones marcadas como leídas para usuario {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error al marcar notificaciones como leídas: {e}")
            await self.session.rollback()
            return False
    
    async def get_recent_notifications(
        self,
        user_id: int,
        bot_id: int,
        limit: int = 10
    ) -> List[dict]:
        """
        Obtiene las notificaciones recientes de un usuario.
        
        Returns:
            Lista de diccionarios con los datos de las notificaciones.
        """
        try:
            stmt = select(Notification).where(
                Notification.user_id == user_id,
                Notification.bot_id == bot_id
            ).order_by(
                Notification.created_at.desc()
            ).limit(limit)
            
            result = await self.session.execute(stmt)
            notifications = result.scalars().all()
            
            return [
                {
                    'id': n.id,
                    'message': n.message,
                    'notification_type': n.notification_type,
                    'created_at': n.created_at,
                    'is_read': n.is_read
                }
                for n in notifications
            ]
        except Exception as e:
            logger.error(f"Error al obtener notificaciones recientes: {e}")
            return []

