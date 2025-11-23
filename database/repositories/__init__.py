"""
Repositories: CAPA DE ACCESO A DATOS
Reemplazan los archivos *_db.py con SQLAlchemy asíncrono.
"""
from .base_repository import BaseRepository
from .extra_module_repository import ExtraModuleRepository
from .user_repository import DoctorRepository, PatientDoctorRepository
from .appointment_repository import SlotRepository, AppointmentRepository
from .content_repository import TextContentRepository, GenericContentRepository
from .location_repository import LocationRepository
from .medical_repository import MedicalRepository
from .pdf_repository import PDFRepository
from .notification_repository import NotificationRepository
from .request_repository import RequestRepository
from .contact_repository import ContactRepository
from .job_repository import JobRepository
from .menu_repository import MainMenuButtonRepository, SubmenuRepository, SubmenuButtonRepository
from .user_util_repository import BotRepository, BotLogoRepository, UserActionRepository

__all__ = [
    'BaseRepository',
    'ExtraModuleRepository',
    'DoctorRepository',
    'PatientDoctorRepository',
    'SlotRepository',
    'AppointmentRepository',
    'TextContentRepository',
    'GenericContentRepository',
    'LocationRepository',
    'MedicalRepository',
    'PDFRepository',
    'NotificationRepository',
    'RequestRepository',
    'ContactRepository',
    'JobRepository',
    'MainMenuButtonRepository',
    'SubmenuRepository',
    'SubmenuButtonRepository',
    'BotRepository',
    'BotLogoRepository',
    'UserActionRepository',
]
