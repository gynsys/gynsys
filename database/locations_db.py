"""
Base de datos para gestión de ubicaciones

⚠️ DEPRECATED: Este módulo está siendo migrado a SQLAlchemy.
Usa database.repositories.location_repository en código nuevo.

Este archivo mantiene compatibilidad durante la migración.
"""
import logging
from database.session import get_session
from database.repositories.location_repository import LocationRepository

logger = logging.getLogger(__name__)


async def get_location_details(loc_id: int):
    """Obtiene todos los detalles de una ubicación por su ID."""
    async with get_session() as session:
        repo = LocationRepository(session)
        return await repo.get_location_details(loc_id)


async def add_location(bot_id: int, name: str, address: str, schedule: str, gmaps_url: str, open_days: str = "0,1,2,3,4"):
    """Añade una nueva ubicación a la base de datos."""
    async with get_session() as session:
        repo = LocationRepository(session)
        await repo.add_location(bot_id, name, address, schedule, gmaps_url, open_days)


async def update_location(loc_id: int, name: str, address: str, schedule: str, gmaps_url: str, open_days: str = None):
    """Actualiza los datos de una ubicación existente."""
    async with get_session() as session:
        repo = LocationRepository(session)
        await repo.update_location(loc_id, name, address, schedule, gmaps_url, open_days)


async def delete_location(loc_id: int):
    """Elimina una ubicación de la base de datos."""
    async with get_session() as session:
        repo = LocationRepository(session)
        await repo.delete_location(loc_id)


async def get_locations_for_bot(bot_id: int):
    """Obtiene todas las ubicaciones activas para un bot/doctor."""
    async with get_session() as session:
        repo = LocationRepository(session)
        return await repo.get_locations_for_bot(bot_id)
