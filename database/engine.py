"""
Configuración del engine asíncrono de SQLAlchemy.
"""
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text
from config import DB_PATH

logger = logging.getLogger(__name__)

# Crear engine asíncrono para SQLite
# Usa aiosqlite como driver asíncrono
engine: AsyncEngine = create_async_engine(
    f"sqlite+aiosqlite:///{DB_PATH}",
    echo=False,  # Cambiar a True para debug SQL
    future=True,
    pool_pre_ping=True,  # Verificar conexiones antes de usarlas
    connect_args={
        "check_same_thread": False,  # Necesario para SQLite asíncrono
        "timeout": 10,
    }
)

async def init_engine():
    """
    Inicializa el engine y ejecuta PRAGMAs necesarios.
    Debe llamarse al inicio de la aplicación.
    """
    async with engine.begin() as conn:
        # Habilitar foreign keys
        await conn.execute(text("PRAGMA foreign_keys = ON;"))
        # Habilitar WAL mode para mejor concurrencia
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
    logger.info("Engine SQLAlchemy inicializado correctamente")

async def close_engine():
    """
    Cierra el engine correctamente.
    Debe llamarse al finalizar la aplicación.
    """
    await engine.dispose()
    logger.info("Engine SQLAlchemy cerrado correctamente")

