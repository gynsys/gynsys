from config import SUPER_ADMIN_ID
from database.session import get_session
from database.repositories.user_repository import DoctorRepository, PatientDoctorRepository
from typing import Optional, Tuple


class RoleManager:
    """
    Manager para determinar roles de usuarios usando SQLAlchemy repositories.
    Todos los métodos son asíncronos.
    """
    
    def __init__(self, db_path=None):
        """
        Args:
            db_path: Mantenido por compatibilidad, no se usa (las sesiones se crean dinámicamente)
        """
        self.db_path = db_path
    
    async def get_user_role(self, telegram_id: int) -> str:
        """
        Determina el rol del usuario con prioridad:
        1. SuperAdmin
        2. Médico (activo o inactivo) 
        3. Paciente
        4. Nuevo usuario
        """
        # 1. SuperAdmin tiene máxima prioridad
        if telegram_id == SUPER_ADMIN_ID:
            return 'superadmin'
        
        async with get_session() as session:
            doctor_repo = DoctorRepository(session)
            patient_doctor_repo = PatientDoctorRepository(session)
            
            # 2. Verificar SIEMPRE si es médico primero (activo o inactivo)
            doctor = await doctor_repo.get_any_doctor_by_telegram_id(telegram_id)
            if doctor:
                if doctor.is_active:
                    return 'doctor'
                else:
                    return 'inactive_doctor'
            
            # 3. Solo si NO es médico, verificar si es paciente
            patient_doctor = await patient_doctor_repo.get_doctor_for_patient(telegram_id)
            if patient_doctor:
                return 'patient'
        
        # 4. Nuevo usuario
        return 'new_user'
    
    async def get_assigned_doctor(self, patient_telegram_id: int) -> Optional[Tuple]:
        """
        Obtiene el médico asignado a un paciente.
        Retorna una tupla (doctor_id, name, telegram_id, is_active, created_at) para compatibilidad.
        """
        # Verificar primero que no sea médico
        doctor = await self.get_doctor_by_telegram_id(patient_telegram_id)
        if doctor:
            return None  # No puede ser paciente si es médico
        
        async with get_session() as session:
            patient_doctor_repo = PatientDoctorRepository(session)
            doctor_obj = await patient_doctor_repo.get_doctor_for_patient(patient_telegram_id)
            
            if doctor_obj:
                # Retornar tupla para compatibilidad con código legacy
                return (
                    doctor_obj.id,
                    doctor_obj.name,
                    doctor_obj.telegram_id,
                    doctor_obj.is_active,
                    doctor_obj.created_at
                )
        return None
    
    async def is_doctor_active(self, telegram_id: int) -> bool:
        """Verifica si un médico está activo"""
        doctor = await self.get_doctor_by_telegram_id(telegram_id)
        return doctor is not None and doctor[3] if doctor else False
    
    async def get_doctor_by_telegram_id(self, telegram_id: int) -> Optional[Tuple]:
        """
        Obtiene médico por Telegram ID (activo o inactivo).
        Retorna una tupla (doctor_id, name, telegram_id, is_active, created_at) para compatibilidad.
        """
        async with get_session() as session:
            doctor_repo = DoctorRepository(session)
            doctor = await doctor_repo.get_any_doctor_by_telegram_id(telegram_id)
            
            if doctor:
                # Retornar tupla para compatibilidad con código legacy
                return (
                    doctor.id,
                    doctor.name,
                    doctor.telegram_id,
                    doctor.is_active,
                    doctor.created_at
                )
        return None
    
    async def get_doctor_by_id(self, doctor_id: int) -> Optional[Tuple]:
        """
        Obtiene médico por ID.
        Retorna una tupla (doctor_id, name, telegram_id, is_active, created_at) para compatibilidad.
        """
        async with get_session() as session:
            doctor_repo = DoctorRepository(session)
            doctor = await doctor_repo.get_doctor_by_id(doctor_id)
            
            if doctor:
                return (
                    doctor.id,
                    doctor.name,
                    doctor.telegram_id,
                    doctor.is_active,
                    doctor.created_at
                )
        return None
    
    async def assign_patient_to_doctor(self, patient_telegram_id: int, doctor_id: int) -> bool:
        """
        Asigna un paciente a un médico.
        """
        async with get_session() as session:
            patient_doctor_repo = PatientDoctorRepository(session)
            await patient_doctor_repo.assign_patient_to_doctor(patient_telegram_id, doctor_id)
            return True