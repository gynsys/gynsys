# Guía de Uso de Repositories

## 📚 Introducción

Los repositories son la capa de acceso a datos que reemplaza los archivos `*_db.py`. Usan SQLAlchemy asíncrono y proporcionan una interfaz más limpia y type-safe.

## 🔧 Uso Básico

### Obtener una Sesión

```python
from database.session import get_session
from database.repositories.extra_module_repository import ExtraModuleRepository

async with get_session() as session:
    repo = ExtraModuleRepository(session)
    # Usar el repository aquí
    # La sesión se cierra automáticamente y hace commit
```

### Ejemplo: ExtraModuleRepository

```python
from database.session import get_session
from database.repositories.extra_module_repository import ExtraModuleRepository

async def example():
    async with get_session() as session:
        repo = ExtraModuleRepository(session)
        
        # Obtener módulos activos de un doctor
        modules = await repo.get_active_modules_for_doctor(doctor_id=1)
        print(f"Módulos activos: {modules}")
        
        # Activar un módulo
        success = await repo.activate_module_for_doctor(
            doctor_id=1,
            module_name='test'
        )
        
        # Verificar si está activo
        is_active = await repo.is_module_active_for_doctor(
            doctor_id=1,
            module_name='test'
        )
        
        # Alternar estado
        await repo.toggle_module_for_doctor(
            doctor_id=1,
            module_name='test'
        )
```

## 🔄 Migración desde `*_db.py`

### Antes (código legacy)

```python
from database import extra_modules_db

modules = await extra_modules_db.get_active_modules_for_doctor(doctor_id)
await extra_modules_db.activate_module_for_doctor(doctor_id, 'test')
```

### Después (usando repository)

```python
from database.session import get_session
from database.repositories.extra_module_repository import ExtraModuleRepository

async with get_session() as session:
    repo = ExtraModuleRepository(session)
    modules = await repo.get_active_modules_for_doctor(doctor_id)
    await repo.activate_module_for_doctor(doctor_id, 'test')
```

### Compatibilidad

El código legacy sigue funcionando. Los archivos `*_db.py` ahora actúan como wrappers que usan los repositories internamente. Esto permite una migración gradual sin romper el código existente.

## 📝 Crear un Nuevo Repository

### 1. Crear el archivo del repository

```python
# database/repositories/my_repository.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models.my_model import MyModel
from database.repositories.base_repository import BaseRepository

class MyRepository(BaseRepository[MyModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(MyModel, session)
    
    async def my_custom_method(self, param: str) -> List[MyModel]:
        """Método personalizado"""
        result = await self.session.execute(
            select(MyModel).where(MyModel.field == param)
        )
        return list(result.scalars().all())
```

### 2. Exportar en `__init__.py`

```python
# database/repositories/__init__.py
from .my_repository import MyRepository

__all__ = [
    # ... otros repositories
    'MyRepository',
]
```

### 3. Usar el repository

```python
from database.session import get_session
from database.repositories.my_repository import MyRepository

async with get_session() as session:
    repo = MyRepository(session)
    results = await repo.my_custom_method("value")
```

## ⚠️ Notas Importantes

1. **Siempre usar `get_session()`**: Proporciona manejo automático de commits y rollbacks.

2. **No compartir sesiones**: Cada operación debe usar su propia sesión o asegurarse de que las sesiones compartidas se manejen correctamente.

3. **Manejo de errores**: Los repositories lanzan excepciones que deben ser manejadas en el código que los usa.

4. **Transacciones**: `get_session()` hace commit automático al salir del context manager. Si necesitas control manual, usa `get_session_no_commit()`.

## 🔗 Referencias

- [BaseRepository](database/repositories/base_repository.py) - Métodos comunes disponibles
- [Session Management](database/session.py) - Gestión de sesiones
- [SQLAlchemy Async Docs](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

