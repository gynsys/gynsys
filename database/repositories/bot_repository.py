"""
Repository para gestión de bots/tenants.
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models.bot import Bot, UserTenant
from database.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)

class BotRepository(BaseRepository[Bot]):
    """
    Repository para operaciones con bots.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(Bot, session)
        
    async def get_bot_by_admin_id(self, admin_user_id: int) -> Optional[Bot]:
        """
        Obtiene el bot asociado a un admin_user_id (doctor).
        """
        result = await self.session.execute(
            select(Bot).where(Bot.admin_user_id == admin_user_id, Bot.is_active == True)
        )
        return result.scalar_one_or_none()
        
    async def get_bot_by_id(self, bot_id: int) -> Optional[Bot]:
        """
        Obtiene un bot por su ID.
        """
        return await self.get_by_id(bot_id)
        
    async def update_logo(self, bot_id: int, file_id: str, media_type: str = 'photo') -> bool:
        """
        Actualiza el logo de un bot.
        """
        try:
            await self.session.execute(
                update(Bot)
                .where(Bot.id == bot_id)
                .values(logo_file_id=file_id, logo_media_type=media_type)
            )
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error actualizando logo del bot {bot_id}: {e}")
            return False

class UserTenantRepository(BaseRepository[UserTenant]):
    """
    Repository para operaciones con asociaciones usuario-tenant.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(UserTenant, session)
        
    async def get_tenant_id_for_user(self, user_id: int) -> Optional[int]:
        """
        Obtiene el bot_id (tenant) asociado a un usuario.
        """
        result = await self.session.execute(
            select(UserTenant.bot_id).where(UserTenant.user_id == user_id)
        )
        row = result.first()
        return row[0] if row else None
