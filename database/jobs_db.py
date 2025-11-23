# database/jobs_db.py
"""
Capa de compatibilidad para jobs_db.py.
Migrado a SQLAlchemy asíncrono usando JobRepository.
"""
import asyncio
import logging
from .session import get_session
from .repositories.job_repository import JobRepository

logger = logging.getLogger(__name__)


async def get_appointments_for_reminder(bot_id: int):
    """Obtiene las citas que necesitan recordatorio."""
    async with get_session() as session:
        repo = JobRepository(session)
        return await repo.get_appointments_for_reminder(bot_id)


async def mark_reminder_sent(appointment_id: int):
    """Marca una cita como que ya se envió el recordatorio."""
    async with get_session() as session:
        repo = JobRepository(session)
        await repo.mark_reminder_sent(appointment_id)


async def mark_past_appointments_as_completed(bot_id: int) -> int:
    """Marca las citas pasadas como completadas."""
    async with get_session() as session:
        repo = JobRepository(session)
        return await repo.mark_past_appointments_as_completed(bot_id)


async def delete_past_pending_appointments(bot_id: int) -> int:
    """
    Elimina todas las citas con estado 'pending' cuya fecha es anterior al día de hoy.
    Devuelve el número de citas eliminadas.
    """
    async with get_session() as session:
        repo = JobRepository(session)
        return await repo.delete_past_pending_appointments(bot_id)