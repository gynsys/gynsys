"""
Módulo de base de datos.
Exporta componentes principales de SQLAlchemy y mantiene compatibilidad con código legacy.
"""
# SQLAlchemy asíncrono (nuevo)
from .engine import engine, init_engine, close_engine
from .session import get_session, get_session_no_commit, AsyncSessionLocal
from .models import Base
from .models import (
    Doctor,
    PatientDoctor,
    Bot,
    UserTenant,
    MedicalHistory,
    Slot,
    Appointment,
    TextContent,
    FAQ,
    Gallery,
    Precio,
    Location,
    PDFSetting,
    ExtraModule,
    TestQuestion,
)
from .repositories import BaseRepository

# Código legacy (mantener durante migración)
from .connection import get_db_connection, init_db

__all__ = [
    # Engine y Session
    'engine',
    'init_engine',
    'close_engine',
    'get_session',
    'get_session_no_commit',
    'AsyncSessionLocal',
    # Base
    'Base',
    # Modelos
    'Doctor',
    'PatientDoctor',
    'Bot',
    'UserTenant',
    'MedicalHistory',
    'Slot',
    'Appointment',
    'TextContent',
    'FAQ',
    'Gallery',
    'Precio',
    'Location',
    'PDFSetting',
    'ExtraModule',
    'TestQuestion',
    # Repositories
    'BaseRepository',
    # Legacy (temporal)
    'get_db_connection',
    'init_db',
]

