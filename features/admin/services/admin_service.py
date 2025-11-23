"""
Servicio de administración: Lógica de médicos y usuarios.
Fusiona lógica de negocio con acceso a datos.
"""
import sqlite3
import aiosqlite
from database.session import get_session
from database.repositories.user_repository import DoctorRepository, PatientDoctorRepository
from config import DB_PATH
from utils.logger import get_logger, perm_logger
from ..utils import generate_share_code


class AdminService:
    """
    Servicio que maneja la lógica de administración de médicos.
    Fusiona lógica de negocio con acceso a datos.
    """
    
    def __init__(self):
        self.logger = get_logger("AdminService")
    
    async def get_all_doctors(self):
        """
        Obtiene todos los médicos activos.
        
        Returns:
            list: Lista de tuplas (id, name, telegram_id, is_active, created_at)
        """
        async with get_session() as session:
            repo = DoctorRepository(session)
            doctors = await repo.get_all_doctors()
            return [
                (d.id, d.name, d.telegram_id, d.is_active, d.created_at)
                for d in doctors
            ]
    
    async def get_inactive_doctors(self):
        """
        Obtiene todos los médicos inactivos.
        
        Returns:
            list: Lista de tuplas (id, name, telegram_id, is_active, created_at)
        """
        async with get_session() as session:
            repo = DoctorRepository(session)
            doctors = await repo.get_inactive_doctors()
            return [
                (d.id, d.name, d.telegram_id, d.is_active, d.created_at)
                for d in doctors
            ]
    
    async def get_doctor_by_id(self, doctor_id):
        """
        Obtiene un médico por su ID.
        
        Args:
            doctor_id: ID del médico
        
        Returns:
            tuple: (id, name, telegram_id, is_active, created_at) o None
        """
        async with get_session() as session:
            repo = DoctorRepository(session)
            doctor = await repo.get_doctor_by_id(doctor_id)
            if doctor:
                return (doctor.id, doctor.name, doctor.telegram_id, doctor.is_active, doctor.created_at)
            return None
    
    async def get_any_doctor_by_telegram_id(self, telegram_id):
        """
        Obtiene un médico por su Telegram ID (activo o inactivo).
        
        Args:
            telegram_id: ID de Telegram del médico
        
        Returns:
            tuple: (id, name, telegram_id, is_active, created_at) o None
        """
        async with get_session() as session:
            repo = DoctorRepository(session)
            doctor = await repo.get_any_doctor_by_telegram_id(telegram_id)
            if doctor:
                return (doctor.id, doctor.name, doctor.telegram_id, doctor.is_active, doctor.created_at)
            return None
    
    async def add_doctor(self, doctor_name, telegram_id):
        """
        Agrega un nuevo médico al sistema.
        
        Args:
            doctor_name: Nombre del médico
            telegram_id: ID de Telegram del médico
        
        Returns:
            int: ID del médico creado
        """
        async with get_session() as session:
            repo = DoctorRepository(session)
            doctor_id = await repo.add_doctor(doctor_name, telegram_id)
            self.logger.info(f"Médico agregado: {doctor_name} (ID: {doctor_id}, Telegram: {telegram_id})")
            perm_logger.log_doctor_added(doctor_name, doctor_id, None)  # TODO: pasar user_id si está disponible
            return doctor_id
    
    async def activate_doctor(self, doctor_id):
        """
        Activa un médico.
        
        Args:
            doctor_id: ID del médico
        """
        async with get_session() as session:
            repo = DoctorRepository(session)
            await repo.activate_doctor(doctor_id)
    
    async def restrict_doctor(self, doctor_id):
        """
        Restringe un médico.
        
        Args:
            doctor_id: ID del médico
        """
        async with get_session() as session:
            repo = DoctorRepository(session)
            await repo.delete_doctor(doctor_id)
    
    async def remove_doctor_permanently(self, doctor_id):
        """
        Elimina permanentemente un médico.
        
        Args:
            doctor_id: ID del médico
        """
        async with get_session() as session:
            repo = DoctorRepository(session)
            await repo.remove_doctor_permanently(doctor_id)
    
    async def cleanup_doctor_patient_associations(self):
        """
        Limpia asociaciones incorrectas entre doctores y pacientes.
        """
        async with get_session() as session:
            repo = DoctorRepository(session)
            await repo.cleanup_doctor_patient_associations()
    
    async def update_doctor_name(self, doctor_id, new_name):
        """
        Actualiza el nombre de un médico.
        
        Args:
            doctor_id: ID del médico
            new_name: Nuevo nombre
        """
        async with get_session() as session:
            from sqlalchemy import update
            from database.models.user import Doctor
            repo = DoctorRepository(session)
            doctor = await repo.get_doctor_by_id(doctor_id)
            if doctor:
                doctor.name = new_name
                await session.flush()
                return True
            return False
    
    async def initialize_tenant_data(self, bot_id, doctor_name):
        """
        Inicializa datos por defecto para un nuevo inquilino.
        
        Args:
            bot_id: ID del bot/tenant
            doctor_name: Nombre del médico
        
        Returns:
            bool: True si se inicializó correctamente
        """
        try:
            from scripts.init_tenant.init_tenant_data import init_tenant_data
            success = await init_tenant_data(bot_id, doctor_name)
            if success:
                self.logger.info(f"✅ Datos por defecto inicializados para bot_id={bot_id}")
            else:
                self.logger.warning(f"⚠️ Error al inicializar datos por defecto para bot_id={bot_id}")
            return success
        except Exception as e:
            self.logger.error(f"❌ Error al inicializar datos por defecto: {e}", exc_info=True)
            return False
    
    async def get_bot_id_for_doctor(self, telegram_id):
        """
        Obtiene el bot_id asociado a un médico.
        
        Args:
            telegram_id: ID de Telegram del médico
        
        Returns:
            int: bot_id o None
        """
        try:
            async with aiosqlite.connect(DB_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(
                    'SELECT id FROM bots WHERE admin_user_id = ?',
                    (telegram_id,)
                )
                result = await cursor.fetchone()
                if result:
                    return result['id']
        except Exception as e:
            self.logger.error(f"Error obteniendo bot_id para telegram_id {telegram_id}: {e}")
        return None
    
    def generate_share_info(self, doctor_id, bot_username):
        """
        Genera información de compartir (código y enlace) para un médico.
        
        Args:
            doctor_id: ID del médico
            bot_username: Username del bot
        
        Returns:
            tuple: (share_code, deeplink)
        """
        share_code = generate_share_code(doctor_id)
        deeplink = f"https://t.me/{bot_username}?start=medico_{doctor_id}"
        return share_code, deeplink
    
    def add_or_reactivate_doctor(self, doctor_name, telegram_id):
        """
        Agrega un médico nuevo o reactiva uno existente.
        
        Args:
            doctor_name: Nombre del médico
            telegram_id: ID de Telegram del médico
        
        Returns:
            tuple: (doctor_id, is_new)
        """
        existing = self.get_any_doctor_by_telegram_id(telegram_id)
        
        if existing:
            doctor_id = existing[0]
            # Actualizar nombre si es diferente
            if existing[1] != doctor_name:
                self.update_doctor_name(doctor_id, doctor_name)
            
            # Activar si está inactivo
            if not existing[3]:  # is_active
                self.activate_doctor(doctor_id)
                self.logger.info(f"Médico reactivado: {doctor_name} (ID: {doctor_id}, Telegram: {telegram_id})")
            else:
                self.logger.info(f"Médico ya existe y está activo: {doctor_name} (ID: {doctor_id}, Telegram: {telegram_id})")
            
            return doctor_id, False
        else:
            # Crear nuevo médico
            doctor_id = self.add_doctor(doctor_name, telegram_id)
            return doctor_id, True

