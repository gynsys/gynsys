"""
Base de datos para gestión de configuración de PDF

⚠️ DEPRECATED: Este módulo está siendo migrado a SQLAlchemy.
Usa database.repositories.pdf_repository en código nuevo.

Este archivo mantiene compatibilidad durante la migración.
"""
import logging
from database.session import get_session
from database.repositories.pdf_repository import PDFRepository, DEFAULT_PDF_SETTINGS

logger = logging.getLogger(__name__)

# Re-exportar DEFAULT_PDF_SETTINGS para compatibilidad
__all__ = [
    'get_pdf_settings',
    'apply_default_settings',
    'update_pdf_setting',
    'toggle_setting_visibility',
    'get_setting_value',
    'DEFAULT_PDF_SETTINGS',
]


async def get_pdf_settings(doctor_id: int) -> dict:
    """Obtiene TODA la configuración de PDF para un doctor específico (multi-tenant)"""
    async with get_session() as session:
        repo = PDFRepository(session)
        return await repo.get_pdf_settings(doctor_id)


async def apply_default_settings(doctor_id: int, current_settings: dict) -> dict:
    """Aplica valores por defecto a configuraciones faltantes"""
    async with get_session() as session:
        repo = PDFRepository(session)
        return await repo.apply_default_settings(doctor_id, current_settings)


async def update_pdf_setting(doctor_id: int, setting_key: str, setting_value: str, is_visible: bool = True) -> bool:
    """Actualiza o crea una configuración de PDF para un doctor (multi-tenant)"""
    async with get_session() as session:
        repo = PDFRepository(session)
        return await repo.update_pdf_setting(doctor_id, setting_key, setting_value, is_visible)


async def toggle_setting_visibility(doctor_id: int, setting_key: str) -> bool:
    """Alterna la visibilidad de una configuración"""
    async with get_session() as session:
        repo = PDFRepository(session)
        return await repo.toggle_setting_visibility(doctor_id, setting_key)


async def get_setting_value(doctor_id: int, setting_key: str) -> str:
    """Obtiene el valor de una configuración específica"""
    async with get_session() as session:
        repo = PDFRepository(session)
        return await repo.get_setting_value(doctor_id, setting_key)
