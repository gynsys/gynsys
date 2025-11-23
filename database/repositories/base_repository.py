"""
Repository base con métodos comunes para todos los repositories.
Proporciona CRUD básico y métodos de consulta comunes.
"""
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from database.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Repository base genérico que proporciona operaciones CRUD comunes.
    
    Uso:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: AsyncSession):
                super().__init__(User, session)
    """
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Args:
            model: Clase del modelo SQLAlchemy
            session: Sesión asíncrona de SQLAlchemy
        """
        self.model = model
        self.session = session
    
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Obtiene un registro por su ID.
        
        Args:
            id: ID del registro
        
        Returns:
            Instancia del modelo o None si no existe
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ModelType]:
        """
        Obtiene todos los registros.
        
        Args:
            limit: Límite de resultados (opcional)
            offset: Offset para paginación
        
        Returns:
            Lista de instancias del modelo
        """
        query = select(self.model).offset(offset)
        if limit:
            query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def create(self, **kwargs) -> ModelType:
        """
        Crea un nuevo registro.
        
        Args:
            **kwargs: Valores para los campos del modelo
        
        Returns:
            Instancia creada del modelo
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()  # Flush para obtener el ID sin commit
        await self.session.refresh(instance)
        return instance
    
    async def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """
        Actualiza un registro existente.
        
        Args:
            id: ID del registro a actualizar
            **kwargs: Campos a actualizar
        
        Returns:
            Instancia actualizada o None si no existe
        """
        instance = await self.get_by_id(id)
        if not instance:
            return None
        
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    
    async def delete(self, id: int) -> bool:
        """
        Elimina un registro por su ID.
        
        Args:
            id: ID del registro a eliminar
        
        Returns:
            True si se eliminó, False si no existía
        """
        instance = await self.get_by_id(id)
        if not instance:
            return False
        
        await self.session.delete(instance)
        await self.session.flush()
        return True
    
    async def count(self) -> int:
        """
        Cuenta el total de registros.
        
        Returns:
            Número total de registros
        """
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0
    
    async def exists(self, id: int) -> bool:
        """
        Verifica si un registro existe.
        
        Args:
            id: ID del registro
        
        Returns:
            True si existe, False en caso contrario
        """
        result = await self.session.execute(
            select(func.count()).select_from(self.model).where(self.model.id == id)
        )
        return (result.scalar() or 0) > 0
    
    async def filter_by(self, **kwargs) -> List[ModelType]:
        """
        Filtra registros por campos específicos.
        
        Args:
            **kwargs: Campos y valores para filtrar
        
        Returns:
            Lista de instancias que coinciden con los filtros
        """
        query = select(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_one_by(self, **kwargs) -> Optional[ModelType]:
        """
        Obtiene un único registro que coincida con los filtros.
        
        Args:
            **kwargs: Campos y valores para filtrar
        
        Returns:
            Primera instancia que coincide o None
        """
        results = await self.filter_by(**kwargs)
        return results[0] if results else None

