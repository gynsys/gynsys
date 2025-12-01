"""
Repository para gestionar solicitudes de doctores.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from .base_repository import BaseRepository
from database.models.request import DoctorRequest
import logging

logger = logging.getLogger(__name__)


class RequestRepository(BaseRepository[DoctorRequest]):
    """
    Repository para operaciones con solicitudes de doctores.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(DoctorRequest, session)
    
    async def create_request(
        self,
        full_name: str,
        telegram_id: int,
        status: str = "pending",
        doctor_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Crea una nueva solicitud de doctor.
        
        Returns:
            ID de la solicitud creada, o None si hay error (ej: constraint único).
        """
        try:
            request = DoctorRequest(
                full_name=full_name,
                telegram_id=telegram_id,
                status=status,
                doctor_id=doctor_id
            )
            self.session.add(request)
            await self.session.flush()
            request_id = request.id
            return request_id
        except Exception as e:
            logger.error(f"Error al crear solicitud: {e}")
            await self.session.rollback()
            return None
    
    async def has_pending_request(self, telegram_id: int) -> bool:
        """
        Verifica si un usuario tiene una solicitud pendiente.
        """
        try:
            stmt = select(DoctorRequest).where(
                DoctorRequest.telegram_id == telegram_id,
                DoctorRequest.status == 'pending'
            ).limit(1)
            
            result = await self.session.execute(stmt)
            request = result.scalar_one_or_none()
            return request is not None
        except Exception as e:
            logger.error(f"Error al verificar solicitud pendiente: {e}")
            return False
    
    async def list_pending(self) -> List[Dict[str, Any]]:
        """
        Lista todas las solicitudes pendientes o diferidas.
        
        Returns:
            Lista de diccionarios con los datos de las solicitudes.
        """
        try:
            stmt = select(DoctorRequest).where(
                DoctorRequest.status.in_(['pending', 'deferred'])
            ).order_by(
                DoctorRequest.created_at.desc()
            )
            
            result = await self.session.execute(stmt)
            requests = result.scalars().all()
            
            return [
                {
                    'id': r.id,
                    'full_name': r.full_name,
                    'telegram_id': r.telegram_id,
                    'status': r.status,
                    'doctor_id': r.doctor_id,
                    'created_at': r.created_at
                }
                for r in requests
            ]
        except Exception as e:
            logger.error(f"Error al listar solicitudes pendientes: {e}")
            return []
    
    async def get_request_by_id(self, request_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene una solicitud por su ID.
        
        Returns:
            Diccionario con los datos de la solicitud, o None si no existe.
        """
        try:
            request = await self.get_by_id(request_id)
            if request:
                return {
                    'id': request.id,
                    'full_name': request.full_name,
                    'telegram_id': request.telegram_id,
                    'status': request.status,
                    'doctor_id': request.doctor_id,
                    'created_at': request.created_at
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener solicitud por ID: {e}")
            return None
    
    async def update_status(
        self,
        request_id: int,
        status: str,
        doctor_id: Optional[int] = None
    ) -> bool:
        """
        Actualiza el estado de una solicitud.
        
        Returns:
            True si se actualizó correctamente, False en caso contrario.
        """
        try:
            request = await self.get_by_id(request_id)
            if not request:
                logger.warning(f"Solicitud {request_id} no encontrada")
                return False
            
            request.status = status
            if doctor_id is not None:
                request.doctor_id = doctor_id
            
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error al actualizar estado de solicitud: {e}")
            await self.session.rollback()
            return False

    async def mark_as_approved(self, request_id: int, doctor_id: int) -> bool:
        """
        Marca una solicitud como aprobada, manejando duplicados anteriores.
        """
        try:
            request = await self.get_by_id(request_id)
            if not request:
                return False
            
            # Buscar solicitudes aprobadas anteriores de este usuario
            stmt = select(DoctorRequest).where(
                DoctorRequest.telegram_id == request.telegram_id,
                DoctorRequest.status == 'approved',
                DoctorRequest.id != request_id
            )
            result = await self.session.execute(stmt)
            previous_approved = result.scalars().all()
            
            # Archivar anteriores para evitar violación de constraint único
            for prev in previous_approved:
                prev.status = f"archived_{prev.id}"
            
            request.status = 'approved'
            request.doctor_id = doctor_id
            
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error al marcar solicitud como aprobada: {e}")
            await self.session.rollback()
            return False

