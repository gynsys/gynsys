"""
Repository para gestión de citas y slots.
Reemplaza appointments_db.py con SQLAlchemy asíncrono.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.orm import selectinload, joinedload
from database.models.appointment import Slot, Appointment
from database.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class SlotRepository(BaseRepository[Slot]):
    """
    Repository para operaciones con slots (cupos de citas).
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(Slot, session)
    
    async def add_slot(
        self, 
        doctor_id: int, 
        start_ts: int, 
        duration_min: int, 
        note: Optional[str] = None
    ) -> Slot:
        """
        Crea un nuevo slot (cupo) para un doctor.
        
        Args:
            doctor_id: ID del doctor
            start_ts: Timestamp Unix de inicio
            duration_min: Duración en minutos
            note: Nota opcional
        
        Returns:
            Instancia de Slot creada
        """
        slot = Slot(
            doctor_id=doctor_id,
            start_ts=start_ts,
            duration_min=duration_min,
            note=note,
            is_active=1
        )
        self.session.add(slot)
        await self.session.flush()
        await self.session.refresh(slot)
        return slot
    
    async def list_active_slots(
        self, 
        doctor_id: int, 
        after_ts: int,
        limit: int = 50
    ) -> List[Slot]:
        """
        Lista slots activos disponibles (sin reservar) para un doctor.
        
        Args:
            doctor_id: ID del doctor
            after_ts: Timestamp mínimo (solo slots después de este tiempo)
            limit: Límite de resultados
        
        Returns:
            Lista de slots disponibles
        """
        # Query: slots activos, sin appointments, después de after_ts
        result = await self.session.execute(
            select(Slot)
            .outerjoin(Appointment, Slot.id == Appointment.slot_id)
            .where(
                Slot.doctor_id == doctor_id,
                Slot.is_active == 1,
                Slot.start_ts >= after_ts,
                Appointment.id.is_(None)  # Sin reserva
            )
            .order_by(Slot.start_ts.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def delete_slot(self, doctor_id: int, slot_id: int) -> bool:
        """
        Elimina un slot si no tiene appointments asociados.
        
        Args:
            doctor_id: ID del doctor
            slot_id: ID del slot
        
        Returns:
            True si se eliminó, False si no se pudo (tiene appointments)
        """
        # Verificar que no tenga appointments
        appointment_result = await self.session.execute(
            select(Appointment).where(Appointment.slot_id == slot_id)
        )
        if appointment_result.scalar_one_or_none():
            return False  # Tiene appointments, no se puede eliminar
        
        # Eliminar el slot
        result = await self.session.execute(
            delete(Slot).where(
                Slot.id == slot_id,
                Slot.doctor_id == doctor_id
            )
        )
        await self.session.flush()
        return result.rowcount > 0
    
    async def get_slot_by_id(self, slot_id: int, doctor_id: int) -> Optional[Slot]:
        """
        Obtiene un slot por su ID, verificando que pertenezca al doctor.
        
        Args:
            slot_id: ID del slot
            doctor_id: ID del doctor
        
        Returns:
            Instancia de Slot o None
        """
        result = await self.session.execute(
            select(Slot).where(
                Slot.id == slot_id,
                Slot.doctor_id == doctor_id
            )
        )
        return result.scalar_one_or_none()


class AppointmentRepository(BaseRepository[Appointment]):
    """
    Repository para operaciones con appointments (citas reservadas).
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(Appointment, session)
        self.slot_repo = SlotRepository(session)
    
    async def book_slot(
        self,
        doctor_id: int,
        slot_id: int,
        patient_telegram_id: int,
        patient_name: str,
        consultation_type: Optional[str] = None,
        reason: Optional[str] = None,
        location: Optional[str] = None,
        status: str = "pending",
        is_first_pregnancy: Optional[bool] = None,
        has_been_pregnant: Optional[bool] = None,
    ) -> bool:
        """
        Reserva un slot para un paciente.
        
        Args:
            doctor_id: ID del doctor
            slot_id: ID del slot a reservar
            patient_telegram_id: Telegram ID del paciente
            patient_name: Nombre del paciente
            consultation_type: Tipo de consulta (opcional)
            reason: Motivo de la consulta (opcional)
            location: Ubicación (opcional)
            status: Estado de la cita (default: "pending")
            is_first_pregnancy: True si es primer embarazo (Prenatal) (opcional)
            has_been_pregnant: True si ha estado embarazada (Ginecológica) (opcional)
        
        Returns:
            True si se reservó correctamente, False si el slot no está disponible
        """
        # Verificar que el slot sea del doctor, activo y sin reservar
        slot = await self.slot_repo.get_slot_by_id(slot_id, doctor_id)
        if not slot or slot.is_active != 1:
            return False
        
        # Verificar que no tenga appointment
        existing = await self.session.execute(
            select(Appointment).where(Appointment.slot_id == slot_id)
        )
        if existing.scalar_one_or_none():
            return False  # Ya está reservado
        
        # Crear el appointment
        appointment = Appointment(
            slot_id=slot_id,
            doctor_id=doctor_id,
            patient_telegram_id=patient_telegram_id,
            patient_name=patient_name,
            consultation_type=consultation_type,
            reason=reason,
            location=location,
            status=status,
            booked_at=int(datetime.utcnow().timestamp()),
            is_first_pregnancy=is_first_pregnancy,
            has_been_pregnant=has_been_pregnant
        )
        self.session.add(appointment)
        await self.session.flush()
        return True
    
    async def get_appointments_for_doctor(
        self, 
        doctor_id: int, 
        statuses: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todas las citas de un doctor, opcionalmente filtradas por estado.
        
        Args:
            doctor_id: ID del doctor
            statuses: Lista de estados para filtrar (opcional)
        
        Returns:
            Lista de diccionarios con información de appointments y slots
        """
        query = (
            select(Appointment, Slot)
            .join(Slot, Appointment.slot_id == Slot.id)
            .where(Appointment.doctor_id == doctor_id)
        )
        
        if statuses:
            query = query.where(Appointment.status.in_(statuses))
        
        query = query.order_by(Slot.start_ts.asc())
        
        result = await self.session.execute(query)
        rows = result.all()
        
        # Convertir a diccionarios para compatibilidad con código legacy
        appointments = []
        for appointment, slot in rows:
            app_dict = {
                'id': appointment.id,
                'slot_id': appointment.slot_id,
                'doctor_id': appointment.doctor_id,
                'patient_telegram_id': appointment.patient_telegram_id,
                'patient_name': appointment.patient_name,
                'consultation_type': appointment.consultation_type,
                'reason': appointment.reason,
                'location': appointment.location,
                'status': appointment.status,
                'booked_at': appointment.booked_at,
                'start_ts': slot.start_ts,
                'duration_min': slot.duration_min,
                'note': slot.note,
            }
            appointments.append(app_dict)
        
        return appointments
    
    async def get_appointment_by_id(
        self, 
        appointment_id: int, 
        doctor_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene una cita por su ID, verificando que pertenezca al doctor.
        
        Args:
            appointment_id: ID de la cita
            doctor_id: ID del doctor
        
        Returns:
            Diccionario con información de la cita y su slot, o None
        """
        result = await self.session.execute(
            select(Appointment, Slot)
            .join(Slot, Appointment.slot_id == Slot.id)
            .where(
                Appointment.id == appointment_id,
                Appointment.doctor_id == doctor_id
            )
        )
        row = result.first()
        
        if not row:
            return None
        
        appointment, slot = row
        return {
            'id': appointment.id,
            'slot_id': appointment.slot_id,
            'doctor_id': appointment.doctor_id,
            'patient_telegram_id': appointment.patient_telegram_id,
            'patient_name': appointment.patient_name,
            'consultation_type': appointment.consultation_type,
            'reason': appointment.reason,
            'location': appointment.location,
            'status': appointment.status,
            'booked_at': appointment.booked_at,
            'start_ts': slot.start_ts,
            'duration_min': slot.duration_min,
            'note': slot.note,
        }
    
    async def update_appointment_status(
        self, 
        appointment_id: int, 
        doctor_id: int, 
        status: str
    ) -> bool:
        """
        Actualiza el estado de una cita.
        
        Args:
            appointment_id: ID de la cita
            doctor_id: ID del doctor
            status: Nuevo estado
        
        Returns:
            True si se actualizó, False si no existe
        """
        result = await self.session.execute(
            update(Appointment)
            .where(
                Appointment.id == appointment_id,
                Appointment.doctor_id == doctor_id
            )
            .values(status=status)
        )
        await self.session.flush()
        return result.rowcount > 0
    
    async def update_appointment_time(
        self, 
        appointment_id: int, 
        doctor_id: int, 
        new_start_ts: int
    ) -> bool:
        """
        Actualiza el tiempo de una cita (modifica el slot asociado).
        
        Args:
            appointment_id: ID de la cita
            doctor_id: ID del doctor
            new_start_ts: Nuevo timestamp de inicio
        
        Returns:
            True si se actualizó, False si no existe
        """
        # Obtener el appointment y su slot_id
        appointment = await self.session.execute(
            select(Appointment).where(
                Appointment.id == appointment_id,
                Appointment.doctor_id == doctor_id
            )
        )
        appointment_obj = appointment.scalar_one_or_none()
        if not appointment_obj:
            return False
        
        # Actualizar el slot
        result = await self.session.execute(
            update(Slot)
            .where(
                Slot.id == appointment_obj.slot_id,
                Slot.doctor_id == doctor_id
            )
            .values(start_ts=new_start_ts)
        )
        await self.session.flush()
        return result.rowcount > 0
    
    async def delete_appointment(
        self, 
        appointment_id: int, 
        doctor_id: int
    ) -> bool:
        """
        Elimina una cita y su slot asociado.
        
        Args:
            appointment_id: ID de la cita
            doctor_id: ID del doctor
        
        Returns:
            True si se eliminó, False si no existe
        """
        # Obtener el appointment
        appointment = await self.session.execute(
            select(Appointment).where(
                Appointment.id == appointment_id,
                Appointment.doctor_id == doctor_id
            )
        )
        appointment_obj = appointment.scalar_one_or_none()
        if not appointment_obj:
            return False
        
        slot_id = appointment_obj.slot_id
        
        # Primero eliminar el appointment (para liberar la FK)
        await self.session.delete(appointment_obj)
        await self.session.flush()  # Flush para asegurar que se elimine primero
        
        # Luego eliminar el slot
        result = await self.session.execute(
            delete(Slot).where(
                Slot.id == slot_id,
                Slot.doctor_id == doctor_id
            )
        )
        
        await self.session.flush()
        return result.rowcount > 0

