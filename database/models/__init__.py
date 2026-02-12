"""
Modelos SQLAlchemy organizados por dominio.
"""
from .base import Base
from .user import Doctor, PatientDoctor
from .bot import Bot, UserTenant
from .medical import MedicalHistory
from .appointment import Slot, Appointment
from .content import TextContent, FAQ, Gallery, Precio
from .location import Location
from .pdf import PDFSetting
from .extra import ExtraModule, TestQuestion
from .notification import Notification
from .request import DoctorRequest
from .contact import ContactInfo
from .job import Cita
from .menu import MainMenuButton, Submenu, SubmenuButton
from .util import BotLogo, UserAction
from .bot_test_result import BotTestResult

# Exportar todos los modelos para Alembic
__all__ = [
    'Base',
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
    'Notification',
    'DoctorRequest',
    'ContactInfo',
    'Cita',
    'MainMenuButton',
    'Submenu',
    'SubmenuButton',
    'BotLogo',
    'BotLogo',
    'UserAction',
    'BotTestResult',
]

