"""
Repository para gestión de usuarios: Doctores y asociaciones paciente-médico.
Reemplaza users_db.py con SQLAlchemy asíncrono.
"""
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from database.models.user import Doctor, PatientDoctor, InstitutionUser
from database.models.bot import Bot, UserTenant
from database.models.content import TextContent, FAQ, Gallery, Precio
from database.models.location import Location
from database.models.menu import MainMenuButton, Submenu, SubmenuButton
from database.models.notification import Notification
from database.models.job import Cita
from database.models.extra import TestQuestion, ExtraModule
from database.models.util import BotLogo, UserAction
from database.repositories.base_repository import BaseRepository
from config import SUPER_ADMIN_ID
import logging

logger = logging.getLogger(__name__)


class DoctorRepository(BaseRepository[Doctor]):
    """
    Repository para operaciones con doctores.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(Doctor, session)
    
    async def get_doctor_by_telegram_id(self, telegram_id: int) -> Optional[Doctor]:
        """
        Obtiene un médico activo por su ID de Telegram.
        
        Args:
            telegram_id: Telegram ID del doctor
        
        Returns:
            Instancia de Doctor o None si no existe o está inactivo
        """
        result = await self.session.execute(
            select(Doctor)
            .where(
                Doctor.telegram_id == telegram_id,
                Doctor.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def get_any_doctor_by_telegram_id(self, telegram_id: int) -> Optional[Doctor]:
        """
        Obtiene un médico (activo o inactivo) por su ID de Telegram.
        
        Args:
            telegram_id: Telegram ID del doctor
        
        Returns:
            Instancia de Doctor o None si no existe
        """
        result = await self.session.execute(
            select(Doctor)
            .where(Doctor.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    async def get_doctor_by_id(self, doctor_id: int) -> Optional[Doctor]:
        """
        Obtiene un médico por su ID de base de datos.
        
        Args:
            doctor_id: ID del doctor
        
        Returns:
            Instancia de Doctor o None si no existe
        """
        return await self.get_by_id(doctor_id)
    
    async def get_all_doctors(self) -> List[Doctor]:
        """
        Obtiene todos los médicos activos, excluyendo al SuperAdmin.
        
        Returns:
            Lista de doctores activos
        """
        result = await self.session.execute(
            select(Doctor)
            .where(
                Doctor.is_active == True,
                Doctor.telegram_id != SUPER_ADMIN_ID
            )
            .order_by(Doctor.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_inactive_doctors(self) -> List[Doctor]:
        """
        Obtiene todos los médicos inactivos (restringidos).
        
        Returns:
            Lista de doctores inactivos
        """
        result = await self.session.execute(
            select(Doctor)
            .where(Doctor.is_active == False)
            .order_by(Doctor.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def add_doctor(self, name: str, telegram_id: int) -> int:
        """
        Agrega un nuevo médico al sistema y crea automáticamente su bot_id (tenant).
        
        Args:
            name: Nombre del doctor
            telegram_id: Telegram ID del doctor
        
        Returns:
            ID del doctor creado
        """
        # 1. Crear el doctor
        doctor = Doctor(
            name=name,
            telegram_id=telegram_id,
            is_active=True
        )
        self.session.add(doctor)
        await self.session.flush()  # Flush para obtener el ID
        
        doctor_id = doctor.id
        
        # 2. Crear automáticamente el bot_id (tenant) para este doctor
        token_placeholder = f'tenant_{doctor_id}_placeholder'
        
        try:
            # Verificar si ya existe un bot para este admin_user_id
            bot_result = await self.session.execute(
                select(Bot).where(Bot.admin_user_id == telegram_id)
            )
            existing_bot = bot_result.scalar_one_or_none()
            
            if existing_bot:
                bot_id = existing_bot.id
            else:
                # Crear nuevo bot
                bot = Bot(
                    doctor_name=name,
                    admin_user_id=telegram_id,
                    token=token_placeholder,
                    is_active=True
                )
                self.session.add(bot)
                await self.session.flush()
                bot_id = bot.id
            
            # 3. Crear entrada en user_tenants para vincular el usuario con su bot
            tenant_result = await self.session.execute(
                select(UserTenant).where(
                    UserTenant.user_id == telegram_id,
                    UserTenant.bot_id == bot_id
                )
            )
            if not tenant_result.scalar_one_or_none():
                user_tenant = UserTenant(
                    user_id=telegram_id,
                    bot_id=bot_id
                )
                self.session.add(user_tenant)
            
            await self.session.flush()
            return doctor_id
            
        except Exception as e:
            logger.warning(f"Error al crear bot_id para doctor {doctor_id}: {e}")
            await self.session.rollback()
            raise
    
    async def delete_doctor(self, doctor_id: int) -> bool:
        """
        Elimina un médico (marca como inactivo).
        
        Args:
            doctor_id: ID del doctor
        
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        doctor = await self.get_by_id(doctor_id)
        if not doctor:
            return False
        
        doctor.is_active = False
        await self.session.flush()
        return True
    
    async def remove_doctor_permanently(self, doctor_id: int) -> bool:
        """
        Elimina un médico y sus asociaciones de todas las tablas.
        
        Args:
            doctor_id: ID del doctor
        
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        doctor = await self.get_by_id(doctor_id)
        if not doctor:
            return False
        
        telegram_id = doctor.telegram_id
        
        try:
            # 1. Obtener el bot_id asociado al doctor
            bot_stmt = select(Bot.id).where(Bot.admin_user_id == telegram_id)
            bot_result = await self.session.execute(bot_stmt)
            bot_id = bot_result.scalar_one_or_none()
            
            # 2. Eliminar de patient_doctor (como doctor y como paciente)
            await self.session.execute(
                delete(PatientDoctor).where(PatientDoctor.doctor_id == doctor_id)
            )
            await self.session.execute(
                delete(PatientDoctor).where(PatientDoctor.patient_telegram_id == telegram_id)
            )
            
            # 3. Eliminar módulos extras (depende de doctor_id, no bot_id)
            await self.session.execute(
                delete(ExtraModule).where(ExtraModule.doctor_id == doctor_id)
            )
            
            # 4. Si existe bot_id, eliminar todas las dependencias del bot ANTES de eliminar el bot
            if bot_id:
                # Eliminar SubmenuButtons primero (dependen de Submenu)
                # Obtener todos los submenu_ids para este bot
                submenu_stmt = select(Submenu.id).where(Submenu.bot_id == bot_id)
                submenu_result = await self.session.execute(submenu_stmt)
                submenu_ids = [row[0] for row in submenu_result.fetchall()]
                
                if submenu_ids:
                    await self.session.execute(
                        delete(SubmenuButton).where(SubmenuButton.submenu_id.in_(submenu_ids))
                    )
                
                # Eliminar todas las tablas que dependen de bot_id
                await self.session.execute(
                    delete(TextContent).where(TextContent.bot_id == bot_id)
                )
                await self.session.execute(
                    delete(FAQ).where(FAQ.bot_id == bot_id)
                )
                await self.session.execute(
                    delete(Gallery).where(Gallery.bot_id == bot_id)
                )
                await self.session.execute(
                    delete(Precio).where(Precio.bot_id == bot_id)
                )
                await self.session.execute(
                    delete(Location).where(Location.bot_id == bot_id)
                )
                await self.session.execute(
                    delete(MainMenuButton).where(MainMenuButton.bot_id == bot_id)
                )
                await self.session.execute(
                    delete(Submenu).where(Submenu.bot_id == bot_id)
                )
                await self.session.execute(
                    delete(Notification).where(Notification.bot_id == bot_id)
                )
                await self.session.execute(
                    delete(Cita).where(Cita.bot_id == bot_id)
                )
                await self.session.execute(
                    delete(TestQuestion).where(TestQuestion.bot_id == bot_id)
                )
                await self.session.execute(
                    delete(BotLogo).where(BotLogo.bot_id == bot_id)
                )
                await self.session.execute(
                    delete(UserAction).where(UserAction.bot_id == bot_id)
                )
                await self.session.execute(
                    delete(UserTenant).where(UserTenant.bot_id == bot_id)
                )
                
                # Ahora sí, eliminar el bot
                await self.session.execute(
                    delete(Bot).where(Bot.id == bot_id)
                )
            else:
                # Si no hay bot_id, solo eliminar user_tenants por user_id
                await self.session.execute(
                    delete(UserTenant).where(UserTenant.user_id == telegram_id)
                )
            
            # 5. Finalmente, eliminar de doctors
            await self.session.delete(doctor)
            await self.session.flush()
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando doctor {doctor_id}: {e}", exc_info=True)
            await self.session.rollback()
            return False
    
    async def restrict_doctor(self, doctor_id: int) -> bool:
        """
        Restringe el acceso de un médico (marca como inactivo).
        
        Args:
            doctor_id: ID del doctor
        
        Returns:
            True si se restringió correctamente, False en caso contrario
        """
        return await self.delete_doctor(doctor_id)
    
    async def activate_doctor(self, doctor_id: int) -> bool:
        """
        Reactiva un médico inactivo.
        
        Args:
            doctor_id: ID del doctor
        
        Returns:
            True si se reactivó correctamente, False en caso contrario
        """
        doctor = await self.get_by_id(doctor_id)
        if not doctor:
            return False
        
        doctor.is_active = True
        await self.session.flush()
        return True
    
    async def cleanup_doctor_patient_associations(self) -> int:
        """
        Elimina asociaciones donde pacientes son también médicos.
        
        Returns:
            Número de asociaciones eliminadas
        """
        # Obtener todos los telegram_ids de doctores
        doctors_result = await self.session.execute(
            select(Doctor.telegram_id)
        )
        doctor_telegram_ids = {row[0] for row in doctors_result.all()}
        
        if not doctor_telegram_ids:
            return 0
        
        # Eliminar asociaciones donde el paciente es también un doctor
        result = await self.session.execute(
            delete(PatientDoctor).where(
                PatientDoctor.patient_telegram_id.in_(doctor_telegram_ids)
            )
        )
        await self.session.flush()
        return result.rowcount


class PatientDoctorRepository(BaseRepository[PatientDoctor]):
    """
    Repository para operaciones con asociaciones paciente-médico.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(PatientDoctor, session)
    
    async def assign_patient_to_doctor(
        self, 
        patient_telegram_id: int, 
        doctor_id: int
    ) -> PatientDoctor:
        """
        Asigna un paciente a un médico.
        Si ya existe la asociación, la actualiza.
        
        Args:
            patient_telegram_id: Telegram ID del paciente
            doctor_id: ID del doctor
        
        Returns:
            Instancia de PatientDoctor creada o actualizada
        """
        # Buscar si ya existe
        result = await self.session.execute(
            select(PatientDoctor).where(
                PatientDoctor.patient_telegram_id == patient_telegram_id,
                PatientDoctor.doctor_id == doctor_id
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing
        
        # Crear nueva asociación
        patient_doctor = PatientDoctor(
            patient_telegram_id=patient_telegram_id,
            doctor_id=doctor_id
        )
        self.session.add(patient_doctor)
        await self.session.flush()
        await self.session.refresh(patient_doctor)
        return patient_doctor
    
    async def get_doctor_for_patient(
        self, 
        patient_telegram_id: int
    ) -> Optional[Doctor]:
        """
        Obtiene el médico asignado a un paciente.
        
        Args:
            patient_telegram_id: Telegram ID del paciente
        
        Returns:
            Instancia de Doctor o None si no tiene doctor asignado
        """
        result = await self.session.execute(
            select(Doctor)
            .join(PatientDoctor, Doctor.id == PatientDoctor.doctor_id)
            .where(
                PatientDoctor.patient_telegram_id == patient_telegram_id,
                Doctor.is_active == True
            )
        )
        return result.scalars().first()
    
    async def get_patients_for_doctor(self, doctor_id: int) -> List[PatientDoctor]:
        """
        Obtiene todos los pacientes asignados a un doctor.
        
        Args:
            doctor_id: ID del doctor
        
        Returns:
            Lista de asociaciones PatientDoctor
        """
        result = await self.session.execute(
            select(PatientDoctor)
            .where(PatientDoctor.doctor_id == doctor_id)
        )
        return list(result.scalars().all())
    
    async def remove_association(
        self, 
        patient_telegram_id: int, 
        doctor_id: int
    ) -> bool:
        """
        Elimina la asociación entre un paciente y un doctor.
        
        Args:
            patient_telegram_id: Telegram ID del paciente
            doctor_id: ID del doctor
        
        Returns:
            True si se eliminó, False si no existía
        """
        result = await self.session.execute(
            delete(PatientDoctor).where(
                PatientDoctor.patient_telegram_id == patient_telegram_id,
                PatientDoctor.doctor_id == doctor_id
            )
        )
        await self.session.flush()
        return result.rowcount > 0


class InstitutionUserRepository(BaseRepository[InstitutionUser]):
    """
    Repository para operaciones con co-usuarios (miembros del equipo de una institución/doctor).
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(InstitutionUser, session)
        
    async def get_institution_user(self, telegram_id: int) -> Optional[InstitutionUser]:
        """
        Obtiene un co-usuario por su telegram_id, incluyendo la relación con el doctor principal (institución).
        """
        result = await self.session.execute(
            select(InstitutionUser)
            .options(selectinload(InstitutionUser.institution))
            .where(InstitutionUser.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
