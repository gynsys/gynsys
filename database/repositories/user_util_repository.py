"""
Repository para funciones de utilidad de usuarios y bots.
Reemplaza user_db.py con SQLAlchemy asíncrono.
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.sqlite import insert
from .base_repository import BaseRepository
from database.models.bot import Bot, UserTenant
from database.models.user import Doctor, PatientDoctor
from database.models.util import BotLogo, UserAction
import logging
import os

logger = logging.getLogger(__name__)


class BotRepository(BaseRepository[Bot]):
    """Repository extendido para operaciones con bots."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Bot, session)
    
    async def get_user_tenant(self, user_id: int) -> Optional[int]:
        """
        Obtiene el tenant_id (bot_id) al que pertenece un usuario.
        Busca en este orden:
        1. Si es admin de algún tenant (médico)
        2. Si está en user_tenants
        3. Si es paciente asignado a un médico
        """
        try:
            # 1. Verifica si es admin de algún tenant
            stmt = select(Bot.id).where(
                Bot.admin_user_id == user_id,
                Bot.is_active == True
            ).limit(1)
            result = await self.session.execute(stmt)
            tenant_id = result.scalar_one_or_none()
            
            if tenant_id:
                return tenant_id
            
            # 2. Verifica en user_tenants
            stmt = select(UserTenant.bot_id).where(
                UserTenant.user_id == user_id
            ).limit(1)
            result = await self.session.execute(stmt)
            tenant_id = result.scalar_one_or_none()
            
            if tenant_id:
                return tenant_id
            
            # 3. Verifica si es paciente asignado a un médico
            stmt = select(Bot.id).join(
                Doctor, Bot.admin_user_id == Doctor.telegram_id
            ).join(
                PatientDoctor, Doctor.id == PatientDoctor.doctor_id
            ).where(
                PatientDoctor.patient_telegram_id == user_id,
                Doctor.is_active == True,
                Bot.is_active == True
            ).limit(1)
            
            result = await self.session.execute(stmt)
            tenant_id = result.scalar_one_or_none()
            
            return tenant_id
        except Exception as e:
            logger.error(f"Error al obtener tenant del usuario: {e}")
            return None
    
    async def is_user_admin_for_bot(self, user_id: int, bot_id: int) -> bool:
        """Verifica si el usuario es admin del bot específico."""
        try:
            stmt = select(Bot).where(
                Bot.id == bot_id,
                Bot.admin_user_id == user_id
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error al verificar admin: {e}")
            return False
    
    async def is_user_an_admin(self, user_id: int) -> bool:
        """Verifica si el usuario es admin de CUALQUIER tenant."""
        try:
            stmt = select(Bot).where(
                Bot.admin_user_id == user_id,
                Bot.is_active == True
            ).limit(1)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error al verificar si es admin: {e}")
            return False
    
    async def get_bot_admin_id(self, bot_id: int) -> Optional[int]:
        """Obtiene el admin_user_id de un bot."""
        try:
            bot = await self.get_by_id(bot_id)
            return bot.admin_user_id if bot else None
        except Exception as e:
            logger.error(f"Error al obtener admin del bot: {e}")
            return None
    
    async def add_new_bot(self, doctor_name: str, admin_user_id: int) -> Optional[int]:
        """Crea un nuevo bot."""
        try:
            bot = Bot(
                doctor_name=doctor_name,
                admin_user_id=admin_user_id,
                token="",  # Se debe generar después
                is_active=True
            )
            self.session.add(bot)
            await self.session.flush()
            return bot.id
        except Exception as e:
            logger.error(f"Error al crear bot: {e}")
            await self.session.rollback()
            return None


class BotLogoRepository(BaseRepository[BotLogo]):
    """Repository para logos de bots."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(BotLogo, session)
    
    async def get_bot_logo_paths(self, bot_id: int) -> Optional[Dict[str, str]]:
        """Obtiene todas las rutas de logos para un bot."""
        try:
            logo = await self.get_by_id(bot_id)
            if logo:
                return {
                    'logo_header_1': logo.logo_header_1,
                    'logo_header_2': logo.logo_header_2,
                    'logo_signature': logo.logo_signature
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener logos: {e}")
            return None
    
    async def update_bot_logo_path(self, bot_id: int, logo_type: str, file_path: str) -> bool:
        """
        Guarda o actualiza la ruta de un logo para un bot.
        
        Args:
            bot_id: ID del bot
            logo_type: 'header1', 'header2', o 'signature'
            file_path: Ruta del archivo
        """
        try:
            column_name_map = {
                'header1': 'logo_header_1',
                'header2': 'logo_header_2',
                'signature': 'logo_signature'
            }
            column_name = column_name_map.get(logo_type)
            if not column_name:
                return False
            
            # Usar INSERT ... ON CONFLICT para upsert
            stmt = insert(BotLogo).values(
                bot_id=bot_id,
                **{column_name: file_path}
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=['bot_id'],
                set_={column_name: stmt.excluded[column_name]}
            )
            
            await self.session.execute(stmt)
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error al actualizar logo: {e}")
            await self.session.rollback()
            return False
    
    async def delete_bot_logo_path(self, bot_id: int, logo_type: str) -> bool:
        """
        Elimina la ruta de un logo de la BD y borra el archivo físico.
        
        Args:
            bot_id: ID del bot
            logo_type: 'header1', 'header2', o 'signature'
        """
        try:
            logo = await self.get_by_id(bot_id)
            if not logo:
                return False
            
            column_name_map = {
                'header1': 'logo_header_1',
                'header2': 'logo_header_2',
                'signature': 'logo_signature'
            }
            column_name = column_name_map.get(logo_type)
            if not column_name:
                return False
            
            # Obtener la ruta del archivo antes de eliminarlo
            file_path = getattr(logo, column_name)
            
            # Borrar el archivo físico si existe
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Archivo de logo eliminado: {file_path}")
            
            # Actualizar la base de datos a None
            setattr(logo, column_name, None)
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error al eliminar logo: {e}")
            await self.session.rollback()
            return False


class UserActionRepository(BaseRepository[UserAction]):
    """Repository para acciones de usuarios."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(UserAction, session)
    
    async def log_user_action(self, user_id: int, bot_id: int, action_key: str, timestamp: int) -> bool:
        """Registra una acción de usuario."""
        try:
            stmt = insert(UserAction).values(
                user_id=user_id,
                bot_id=bot_id,
                action_key=action_key,
                timestamp=timestamp
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=['user_id', 'bot_id', 'action_key'],
                set_={'timestamp': stmt.excluded.timestamp}
            )
            
            await self.session.execute(stmt)
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error al registrar acción: {e}")
            await self.session.rollback()
            return False
    
    async def get_last_action_timestamp(self, user_id: int, bot_id: int, action_key: str) -> Optional[int]:
        """Obtiene el timestamp de la última vez que un usuario realizó una acción."""
        try:
            stmt = select(UserAction.timestamp).where(
                UserAction.user_id == user_id,
                UserAction.bot_id == bot_id,
                UserAction.action_key == action_key
            )
            result = await self.session.execute(stmt)
            row = result.first()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error al obtener timestamp: {e}")
            return None
    
    async def has_user_completed_action(self, user_id: int, bot_id: int, action_key: str) -> bool:
        """Verifica si un usuario ha completado una acción."""
        try:
            stmt = select(UserAction).where(
                UserAction.user_id == user_id,
                UserAction.bot_id == bot_id,
                UserAction.action_key == action_key
            ).limit(1)
            
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as e:
            logger.error(f"Error al verificar acción: {e}")
            return False

