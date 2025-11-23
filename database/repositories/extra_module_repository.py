"""
Repository para gestión de módulos extras por doctor.
Reemplaza extra_modules_db.py con SQLAlchemy asíncrono.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from database.models.extra import ExtraModule
from database.models.user import Doctor
from database.repositories.base_repository import BaseRepository


class ExtraModuleRepository(BaseRepository[ExtraModule]):
    """
    Repository para operaciones con módulos extras.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(ExtraModule, session)
    
    async def get_active_modules_for_doctor(self, doctor_id: int) -> List[str]:
        """
        Obtiene todos los módulos activos para un doctor.
        
        Args:
            doctor_id: ID del doctor
        
        Returns:
            Lista de nombres de módulos activos
        """
        result = await self.session.execute(
            select(ExtraModule.module_name)
            .where(
                ExtraModule.doctor_id == doctor_id,
                ExtraModule.is_active == True
            )
        )
        return [row[0] for row in result.all()]
    
    async def is_module_active_for_doctor(self, doctor_id: int, module_name: str) -> bool:
        """
        Verifica si un módulo está activo para un doctor.
        
        Args:
            doctor_id: ID del doctor
            module_name: Nombre del módulo
        
        Returns:
            True si está activo, False en caso contrario
        """
        result = await self.session.execute(
            select(ExtraModule.is_active)
            .where(
                ExtraModule.doctor_id == doctor_id,
                ExtraModule.module_name == module_name
            )
        )
        row = result.first()
        return row[0] == True if row else False
    
    async def activate_module_for_doctor(self, doctor_id: int, module_name: str) -> bool:
        """
        Activa un módulo para un doctor.
        Si el módulo no existe, lo crea. Si existe, lo activa.
        
        Args:
            doctor_id: ID del doctor
            module_name: Nombre del módulo
        
        Returns:
            True si se activó correctamente, False en caso contrario
        """
        try:
            # Buscar si ya existe
            result = await self.session.execute(
                select(ExtraModule)
                .where(
                    ExtraModule.doctor_id == doctor_id,
                    ExtraModule.module_name == module_name
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Actualizar si existe
                existing.is_active = True
            else:
                # Crear si no existe
                new_module = ExtraModule(
                    doctor_id=doctor_id,
                    module_name=module_name,
                    is_active=True
                )
                self.session.add(new_module)
            
            await self.session.flush()
            return True
        except Exception as e:
            print(f"Error activando módulo: {e}")
            await self.session.rollback()
            return False
    
    async def deactivate_module_for_doctor(self, doctor_id: int, module_name: str) -> bool:
        """
        Desactiva un módulo para un doctor.
        
        Args:
            doctor_id: ID del doctor
            module_name: Nombre del módulo
        
        Returns:
            True si se desactivó correctamente, False en caso contrario
        """
        try:
            result = await self.session.execute(
                update(ExtraModule)
                .where(
                    ExtraModule.doctor_id == doctor_id,
                    ExtraModule.module_name == module_name
                )
                .values(is_active=False)
            )
            await self.session.flush()
            return result.rowcount > 0
        except Exception as e:
            print(f"Error desactivando módulo: {e}")
            await self.session.rollback()
            return False
    
    async def toggle_module_for_doctor(self, doctor_id: int, module_name: str) -> bool:
        """
        Alterna el estado de un módulo para un doctor.
        
        Args:
            doctor_id: ID del doctor
            module_name: Nombre del módulo
        
        Returns:
            True si se alternó correctamente, False en caso contrario
        """
        is_active = await self.is_module_active_for_doctor(doctor_id, module_name)
        if is_active:
            return await self.deactivate_module_for_doctor(doctor_id, module_name)
        else:
            return await self.activate_module_for_doctor(doctor_id, module_name)
    
    async def get_all_doctors_with_modules(self) -> List[dict]:
        """
        Obtiene todos los doctores (activos e inactivos) con sus módulos activos.
        Excluye al SuperAdmin (id=1).
        
        Returns:
            Lista de diccionarios con información de doctores y sus módulos
        """
        # Obtener todos los doctores (activos e inactivos) excepto SuperAdmin
        # Esto permite al superadmin gestionar módulos de todos los médicos
        from config import SUPER_ADMIN_ID
        doctors_result = await self.session.execute(
            select(Doctor)
            .where(
                Doctor.telegram_id != SUPER_ADMIN_ID  # Excluir SuperAdmin por telegram_id
            )
            .order_by(Doctor.name)
        )
        doctors = doctors_result.scalars().all()
        
        # Para cada doctor, obtener sus módulos activos
        result = []
        for doctor in doctors:
            modules_result = await self.session.execute(
                select(ExtraModule.module_name)
                .where(
                    ExtraModule.doctor_id == doctor.id,
                    ExtraModule.is_active == True
                )
            )
            modules = [row[0] for row in modules_result.all()]
            
            result.append({
                'doctor_id': doctor.id,
                'name': doctor.name,
                'telegram_id': doctor.telegram_id,
                'modules': modules
            })
        
        return result
    
    async def get_available_modules(self) -> List[dict]:
        """
        Obtiene la lista de módulos disponibles en el sistema.
        Esta es una lista estática que define los módulos disponibles.
        
        Returns:
            Lista de diccionarios con información de módulos disponibles
        """
        return [
            {
                'name': 'galeria',
                'display_name': '🖼️ Galería',
                'description': 'Galería de imágenes y contenido visual'
            },
            {
                'name': 'contacto',
                'display_name': '📞 Contacto',
                'description': 'Información de contacto del médico'
            },
            {
                'name': 'precios',
                'display_name': '💰 Precios',
                'description': 'Lista de precios y servicios'
            },
            {
                'name': 'faqs',
                'display_name': '❓ FAQs',
                'description': 'Preguntas frecuentes'
            },
            {
                'name': 'citas',
                'display_name': '📅 Citas',
                'description': 'Sistema de gestión de citas'
            },
            {
                'name': 'ubicaciones',
                'display_name': '📍 Ubicaciones',
                'description': 'Ubicaciones y horarios de consultorios'
            },
            {
                'name': 'test',
                'display_name': '🧪 Test Endometriosis',
                'description': 'Módulo de pruebas médicas'
            },
            {
                'name': 'quiz',
                'display_name': '🎮 Aprende Jugando',
                'description': 'Quiz educativo de mitos y verdades'
            },
        ]

