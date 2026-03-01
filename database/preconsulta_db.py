"""
Base de datos para gestión de historiales médicos (preconsultas)

⚠️ DEPRECATED: Este módulo está siendo migrado a SQLAlchemy.
Usa database.repositories.medical_repository en código nuevo.

Este archivo mantiene compatibilidad durante la migración.
"""
import logging
from typing import Optional
from datetime import datetime
from database.session import get_session
from database.repositories.medical_repository import MedicalRepository, SENSITIVE_FIELDS

logger = logging.getLogger(__name__)

# Re-exportar SENSITIVE_FIELDS para compatibilidad
__all__ = [
    'delete_history',
    'get_latest_completed_histories',
    'search_completed_histories_by_name',
    'check_if_user_is_recurrent',
    'save_history',
    'get_all_histories',
    'get_history_details',
    'complete_history',
    'get_patient_history_list',
    'update_history_field',
    'get_next_history_number',
    'save_history_number',
    'SENSITIVE_FIELDS',
    'get_completed_histories_count',
]


async def delete_history(history_id: int) -> bool:
    """Elimina un registro de historial médico por su ID."""
    async with get_session() as session:
        repo = MedicalRepository(session)
        return await repo.delete_history(history_id)


async def get_latest_completed_histories(doctor_id: int, offset: int = 0, limit: int = 7) -> list:
    """Obtiene los 'limit' historiales más recientes con estado 'completed'."""
    async with get_session() as session:
        repo = MedicalRepository(session)
        return await repo.get_latest_completed_histories(doctor_id, offset, limit)


async def get_completed_histories_count(doctor_id: int) -> int:
    """Obtiene la cantidad total de historiales completados para un doctor."""
    async with get_session() as session:
        repo = MedicalRepository(session)
        return await repo.get_completed_histories_count(doctor_id)


async def search_completed_histories_by_name(doctor_id: int, search_term: str) -> list:
    """Busca pacientes por nombre entre los historiales con estado 'completed'."""
    async with get_session() as session:
        repo = MedicalRepository(session)
        return await repo.search_completed_histories_by_name(doctor_id, search_term)


async def check_if_user_is_recurrent(user_id: int, doctor_id: int) -> dict | None:
    """Verifica si un usuario ya tiene un historial médico completo."""
    async with get_session() as session:
        repo = MedicalRepository(session)
        return await repo.check_if_user_is_recurrent(user_id, doctor_id)


async def save_history(data: dict) -> int | None:
    """Guarda un nuevo registro de historia médica en la base de datos."""
    async with get_session() as session:
        repo = MedicalRepository(session)
        return await repo.save_history(data)


async def get_all_histories(doctor_id: int, offset: int = 0, limit: int = 10):
    """Obtiene una lista paginada de todas las historias médicas pendientes."""
    async with get_session() as session:
        repo = MedicalRepository(session)
        return await repo.get_all_histories(doctor_id, offset, limit)


async def get_history_details(history_id: int, doctor_id: int):
    """Obtiene todos los detalles de una historia médica específica por su ID."""
    async with get_session() as session:
        repo = MedicalRepository(session)
        return await repo.get_history_details(history_id, doctor_id)


async def complete_history(history_id: int, doctor_id: int, admin_data: dict) -> bool:
    """Actualiza una historia médica con los datos del admin y cambia el estado a 'completed'."""
    async with get_session() as session:
        repo = MedicalRepository(session)
        return await repo.complete_history(history_id, doctor_id, admin_data)


async def get_patient_history_list(doctor_id: int, user_id: int) -> list:
    """Obtiene la lista de todos los informes completados para un paciente específico."""
    async with get_session() as session:
        repo = MedicalRepository(session)
        return await repo.get_patient_history_list(doctor_id, user_id)


async def update_history_field(history_id: int, field: str, value: str) -> bool:
    """Actualiza un campo específico de un historial médico."""
    async with get_session() as session:
        repo = MedicalRepository(session)
        return await repo.update_history_field(history_id, field, value)


async def get_next_history_number(doctor_id: int, consult_type: str) -> str:
    """Genera el siguiente número de historia correlativo en el formato T-YYYYMM-XXX."""
    async with get_session() as session:
        repo = MedicalRepository(session)
        return await repo.get_next_history_number(doctor_id, consult_type)


async def save_history_number(history_id: int, history_number: str) -> bool:
    """Guarda el número de historia generado en un registro existente."""
    async with get_session() as session:
        repo = MedicalRepository(session)
        return await repo.save_history_number(history_id, history_number)
