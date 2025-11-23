"""
Repository para gestionar trabajos programados (recordatorios, mantenimiento).
Usa la tabla legacy 'citas' para compatibilidad.
"""
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, text
from .base_repository import BaseRepository
from database.models.job import Cita
import logging

logger = logging.getLogger(__name__)


class JobRepository(BaseRepository[Cita]):
    """
    Repository para operaciones de trabajos programados.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(Cita, session)
    
    async def get_appointments_for_reminder(self, bot_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene las citas que necesitan recordatorio.
        
        Returns:
            Lista de diccionarios con los datos de las citas.
        """
        try:
            stmt = select(Cita).where(
                Cita.bot_id == bot_id,
                Cita.status.in_(['pending', 'confirmed']),
                Cita.reminder_sent == False
            )
            
            result = await self.session.execute(stmt)
            citas = result.scalars().all()
            
            return [
                {
                    'id': c.id,
                    'user_id': c.user_id,
                    'user_name': c.user_name,
                    'fecha': c.fecha,
                    'hora': c.hora,
                    'ubicacion': c.ubicacion
                }
                for c in citas
            ]
        except Exception as e:
            logger.error(f"Error al obtener citas para recordatorio: {e}")
            return []
    
    async def mark_reminder_sent(self, appointment_id: int) -> bool:
        """
        Marca una cita como que ya se envió el recordatorio.
        
        Returns:
            True si se actualizó correctamente, False en caso contrario.
        """
        try:
            cita = await self.get_by_id(appointment_id)
            if not cita:
                logger.warning(f"Cita {appointment_id} no encontrada")
                return False
            
            cita.reminder_sent = True
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error al marcar recordatorio enviado: {e}")
            await self.session.rollback()
            return False
    
    async def mark_past_appointments_as_completed(self, bot_id: int) -> int:
        """
        Marca las citas pasadas como completadas.
        
        Returns:
            Número de citas actualizadas.
        """
        try:
            # Usar SQL raw para date() de SQLite
            stmt = update(Cita).where(
                and_(
                    Cita.bot_id == bot_id,
                    Cita.status == 'confirmed',
                    text("fecha < date('now', 'localtime')")
                )
            ).values(status='completed')
            
            result = await self.session.execute(stmt)
            await self.session.flush()
            rows_affected = result.rowcount
            return rows_affected
        except Exception as e:
            logger.error(f"Error al marcar citas pasadas como completadas: {e}")
            await self.session.rollback()
            return 0
    
    async def delete_past_pending_appointments(self, bot_id: int) -> int:
        """
        Elimina todas las citas con estado 'pending' cuya fecha es anterior al día de hoy.
        
        Returns:
            Número de citas eliminadas.
        """
        try:
            # Usar SQL raw para date() de SQLite
            stmt = delete(Cita).where(
                and_(
                    Cita.bot_id == bot_id,
                    Cita.status == 'pending',
                    text("fecha < date('now', 'localtime')")
                )
            )
            
            result = await self.session.execute(stmt)
            await self.session.flush()
            rows_affected = result.rowcount
            return rows_affected
        except Exception as e:
            logger.error(f"Error al eliminar citas pasadas pendientes: {e}")
            await self.session.rollback()
            return 0

