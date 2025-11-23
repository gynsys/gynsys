"""
Base de datos para gestión de módulos extras por doctor

⚠️ DEPRECATED: Este módulo está siendo migrado a SQLAlchemy.
Usa database.repositories.extra_module_repository en código nuevo.

Este archivo mantiene compatibilidad durante la migración.
"""
import logging
from database.session import get_session
from database.repositories.extra_module_repository import ExtraModuleRepository

logger = logging.getLogger(__name__)

# Mantener la misma interfaz para compatibilidad
async def get_active_modules_for_doctor(doctor_id: int) -> list:
    """Obtiene todos los módulos activos para un doctor"""
    async with get_session() as session:
        repo = ExtraModuleRepository(session)
        return await repo.get_active_modules_for_doctor(doctor_id)


async def is_module_active_for_doctor(doctor_id: int, module_name: str) -> bool:
    """Verifica si un módulo está activo para un doctor"""
    async with get_session() as session:
        repo = ExtraModuleRepository(session)
        return await repo.is_module_active_for_doctor(doctor_id, module_name)


async def activate_module_for_doctor(doctor_id: int, module_name: str) -> bool:
    """Activa un módulo para un doctor"""
    async with get_session() as session:
        repo = ExtraModuleRepository(session)
        return await repo.activate_module_for_doctor(doctor_id, module_name)


async def deactivate_module_for_doctor(doctor_id: int, module_name: str) -> bool:
    """Desactiva un módulo para un doctor"""
    async with get_session() as session:
        repo = ExtraModuleRepository(session)
        return await repo.deactivate_module_for_doctor(doctor_id, module_name)


async def toggle_module_for_doctor(doctor_id: int, module_name: str) -> bool:
    """Alterna el estado de un módulo para un doctor"""
    async with get_session() as session:
        repo = ExtraModuleRepository(session)
        return await repo.toggle_module_for_doctor(doctor_id, module_name)


async def get_all_doctors_with_modules() -> list:
    """Obtiene todos los doctores con sus módulos activos"""
    async with get_session() as session:
        repo = ExtraModuleRepository(session)
        return await repo.get_all_doctors_with_modules()


async def get_available_modules() -> list:
    """Obtiene la lista de módulos disponibles en el sistema"""
    async with get_session() as session:
        repo = ExtraModuleRepository(session)
        return await repo.get_available_modules()
