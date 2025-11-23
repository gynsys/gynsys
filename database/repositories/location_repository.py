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
            'display_order': location.display_order
        }
    
    async def add_location(
        self, 
        bot_id: int, 
        name: str, 
        address: str, 
        schedule: str, 
        gmaps_url: str
    ) -> Location:
        """
        Añade una nueva ubicación a la base de datos.
        
        Args:
            bot_id: ID del bot
            name: Nombre de la ubicación
            address: Dirección
            schedule: Horario
            gmaps_url: URL de Google Maps
        
        Returns:
            Instancia de Location creada
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
            display_order=max_order + 1
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
        gmaps_url: str
    ) -> bool:
        """
        Actualiza los datos de una ubicación existente.
        
        Args:
            loc_id: ID de la ubicación
            name: Nuevo nombre
            address: Nueva dirección
            schedule: Nuevo horario
            gmaps_url: Nueva URL de Google Maps
        
        Returns:
            True si se actualizó correctamente, False si no existe
        """
        location = await self.get_by_id(loc_id)
        if not location:
            return False
        
        location.name = name
        location.address = address
        location.schedule = schedule
        location.Maps_url = gmaps_url
        
        await self.session.flush()
        return True
    
    async def delete_location(self, loc_id: int) -> bool:
        """
        Elimina una ubicación de la base de datos.
        
        Args:
            loc_id: ID de la ubicación
        
        Returns:
            True si se eliminó correctamente, False si no existe
        """
        return await self.delete(loc_id)
    
    async def get_locations_for_bot(self, bot_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las ubicaciones activas para un bot/doctor.
        
        Args:
            bot_id: ID del bot
        
        Returns:
            Lista de diccionarios con detalles de ubicaciones activas
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
                'display_order': loc.display_order
            }
            for loc in locations
        ]
