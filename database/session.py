"""
Session factory y context managers para SQLAlchemy asíncrono.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from .engine import engine

logger = logging.getLogger(__name__)

# Session factory asíncrono
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # No expirar objetos después de commit
    autocommit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager para obtener una sesión asíncrona.
    
    Uso:
        async with get_session() as session:
            # Usar session aquí
            pass
        # Session se cierra automáticamente
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_no_commit() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager para obtener una sesión sin auto-commit.
    Útil cuando necesitas controlar manualmente el commit.
    
    Uso:
        async with get_session_no_commit() as session:
            # Hacer operaciones
            await session.commit()  # Commit manual
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

