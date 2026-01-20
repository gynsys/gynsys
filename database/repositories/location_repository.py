"""
Repository para gestión de ubicaciones.
Reemplaza locations_db.py con SQLAlchemy asíncrono.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from database.models.location import Location
from database.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)


class LocationRepository(BaseRepository[Location]):
    """
    Repository para operaciones con ubicaciones.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(Location, session)
    
    async def get_location_details(self, loc_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene todos los detalles de una ubicación por su ID.
        
        Args:
            loc_id: ID de la ubicación
        
        Returns:
            Diccionario con detalles de la ubicación o None si no existe
        """
        location = await self.get_by_id(loc_id)
        if not location:
            return None
        
        return {
            'id': location.id,
            'bot_id': location.bot_id,
            'name': location.name,
            'address': location.address,
            'schedule': location.schedule,
            'Maps_url': location.Maps_url,
            'is_active': location.is_active,
            'display_order': location.display_order,
            'open_days': location.open_days
        }
    
    async def add_location(
        self, 
        bot_id: int, 
        name: str, 
        address: str, 
        schedule: str, 
        gmaps_url: str,
        open_days: str = "0,1,2,3,4"
    ) -> Location:
        """
        Añade una nueva ubicación a la base de datos.
        """
        # Obtener max display_order
        result = await self.session.execute(
            select(Location.display_order)
            .where(Location.bot_id == bot_id)
            .order_by(Location.display_order.desc())
            .limit(1)
        )
        row = result.first()
        max_order = row[0] if row and row[0] is not None else 0
        
        location = Location(
            bot_id=bot_id,
            name=name,
            address=address,
            schedule=schedule,
            Maps_url=gmaps_url,
            is_active=True,
            display_order=max_order + 1,
            open_days=open_days
        )
        self.session.add(location)
        await self.session.flush()
        await self.session.refresh(location)
        return location
    
    async def update_location(
        self, 
        loc_id: int, 
        name: str, 
        address: str, 
        schedule: str, 
        gmaps_url: str,
        open_days: str = None
    ) -> bool:
        """
        Actualiza los datos de una ubicación existente.
        """
        location = await self.get_by_id(loc_id)
        if not location:
            return False
        
        location.name = name
        location.address = address
        location.schedule = schedule
        location.Maps_url = gmaps_url
        if open_days is not None:
            location.open_days = open_days
        
        await self.session.flush()
        return True
    
    async def delete_location(self, loc_id: int) -> bool:
        """
        Elimina una ubicación de la base de datos.
        """
        return await self.delete(loc_id)
    
    async def get_locations_for_bot(self, bot_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las ubicaciones activas para un bot/doctor.
        """
        result = await self.session.execute(
            select(Location)
            .where(
                Location.bot_id == bot_id,
                Location.is_active == True
            )
            .order_by(Location.display_order)
        )
        locations = result.scalars().all()
        
        return [
            {
                'id': loc.id,
                'bot_id': loc.bot_id,
                'name': loc.name,
                'address': loc.address,
                'schedule': loc.schedule,
                'Maps_url': loc.Maps_url,
                'is_active': loc.is_active,
                'display_order': loc.display_order,
                'open_days': loc.open_days
            }
            for loc in locations
        ]
