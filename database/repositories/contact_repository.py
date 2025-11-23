"""
Repository para gestionar información de contacto de doctores.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from .base_repository import BaseRepository
from database.models.contact import ContactInfo
import logging

logger = logging.getLogger(__name__)


class ContactRepository(BaseRepository[ContactInfo]):
    """
    Repository para operaciones con información de contacto.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(ContactInfo, session)
    
    async def get_contact(self, doctor_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene la información de contacto de un doctor.
        
        Returns:
            Diccionario con los datos de contacto, o None si no existe.
        """
        try:
            stmt = select(ContactInfo).where(ContactInfo.doctor_id == doctor_id)
            result = await self.session.execute(stmt)
            contact = result.scalar_one_or_none()
            
            if contact:
                return {
                    'id': contact.id,
                    'doctor_id': contact.doctor_id,
                    'phone': contact.phone,
                    'whatsapp': contact.whatsapp,
                    'email': contact.email,
                    'address': contact.address,
                    'website': contact.website,
                    'updated_at': contact.updated_at
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener contacto: {e}")
            return None
    
    async def upsert_contact(self, doctor_id: int, **fields) -> bool:
        """
        Inserta o actualiza los datos de contacto para un doctor.
        
        Args:
            doctor_id: ID del doctor
            **fields: Campos a actualizar (phone, whatsapp, email, address, website)
        
        Returns:
            True si se actualizó correctamente, False en caso contrario.
        """
        try:
            # Campos permitidos
            allowed_fields = {'phone', 'whatsapp', 'email', 'address', 'website'}
            filtered_fields = {k: v for k, v in fields.items() if k in allowed_fields}
            
            # Actualizar updated_at
            filtered_fields['updated_at'] = datetime.utcnow()
            
            # Usar INSERT ... ON CONFLICT para upsert (SQLite)
            stmt = insert(ContactInfo).values(
                doctor_id=doctor_id,
                **filtered_fields
            )
            
            # En caso de conflicto (doctor_id ya existe), actualizar los campos
            update_dict = {k: stmt.excluded[k] for k in filtered_fields.keys()}
            stmt = stmt.on_conflict_do_update(
                index_elements=['doctor_id'],
                set_=update_dict
            )
            
            await self.session.execute(stmt)
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error al upsert contacto: {e}")
            await self.session.rollback()
            return False
    
    async def update_field(self, doctor_id: int, field: str, value: Optional[str]) -> bool:
        """
        Actualiza un campo específico de contacto.
        
        Args:
            doctor_id: ID del doctor
            field: Nombre del campo (phone, whatsapp, email, address, website)
            value: Nuevo valor
        
        Returns:
            True si se actualizó correctamente, False en caso contrario.
        """
        if field not in {"phone", "whatsapp", "email", "address", "website"}:
            raise ValueError("Campo de contacto no permitido")
        
        return await self.upsert_contact(doctor_id, **{field: value})

