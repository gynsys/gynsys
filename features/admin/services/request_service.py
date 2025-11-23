"""
Servicio de solicitudes: Lógica de solicitudes de médicos.
Fusiona lógica de negocio con acceso a datos.
"""
from database.session import get_session
from database.repositories.request_repository import RequestRepository
from config import DB_PATH
from utils.logger import get_logger
from ..utils import generate_share_code


class RequestService:
    """
    Servicio que maneja la lógica de solicitudes de médicos.
    Fusiona lógica de negocio con acceso a datos.
    """
    
    def __init__(self):
        self.logger = get_logger("RequestService")
    
    async def list_pending(self):
        """
        Lista todas las solicitudes pendientes.
        
        Returns:
            list: Lista de diccionarios con datos de solicitudes
        """
        async with get_session() as session:
            repo = RequestRepository(session)
            return await repo.list_pending()
    
    async def get_request_by_id(self, request_id):
        """
        Obtiene una solicitud por su ID.
        
        Args:
            request_id: ID de la solicitud
        
        Returns:
            dict: Datos de la solicitud o None
        """
        async with get_session() as session:
            repo = RequestRepository(session)
            return await repo.get_request_by_id(request_id)
    
    async def update_status(self, request_id, status, doctor_id=None):
        """
        Actualiza el estado de una solicitud.
        
        Args:
            request_id: ID de la solicitud
            status: Nuevo estado ('approved', 'deferred', etc.)
            doctor_id: ID del médico asociado (opcional)
        """
        async with get_session() as session:
            repo = RequestRepository(session)
            await repo.update_status(request_id, status, doctor_id)
    
    async def approve_request(self, request_id, admin_service):
        """
        Aprueba una solicitud y crea/reactiva el médico.
        
        Args:
            request_id: ID de la solicitud
            admin_service: Instancia de AdminService
        
        Returns:
            tuple: (doctor_id, full_name, telegram_id) o None si falla
        """
        request = await self.get_request_by_id(request_id)
        if not request or request["status"] != "pending":
            return None
        
        telegram_id = request["telegram_id"]
        full_name = request["full_name"]
        
        # Agregar o reactivar médico
        doctor_id, is_new = await admin_service.add_or_reactivate_doctor(full_name, telegram_id)
        
        # Inicializar datos por defecto solo si es nuevo doctor
        if is_new:
            self.logger.info(f"🆕 Doctor nuevo creado (ID: {doctor_id}), inicializando datos por defecto...")
            bot_id = await admin_service.get_bot_id_for_doctor(telegram_id)
            if bot_id:
                self.logger.info(f"📦 Bot_id encontrado: {bot_id}, iniciando carga de datos...")
                success = await admin_service.initialize_tenant_data(bot_id, full_name)
                if success:
                    self.logger.info(f"✅ Datos inicializados correctamente para bot_id={bot_id}")
                else:
                    self.logger.warning(f"⚠️ Error al inicializar datos para bot_id={bot_id}")
            else:
                self.logger.warning(f"⚠️ No se encontró bot_id para telegram_id={telegram_id} después de crear doctor")
        else:
            self.logger.info(f"♻️ Doctor existente reactivado (ID: {doctor_id}), no se inicializan datos")
        
        # Limpiar asociaciones incorrectas
        await admin_service.cleanup_doctor_patient_associations()
        
        # Actualizar estado de la solicitud
        await self.update_status(request_id, "approved", doctor_id)
        
        return doctor_id, full_name, telegram_id
    
    async def reject_request(self, request_id):
        """
        Rechaza/pospone una solicitud.
        
        Args:
            request_id: ID de la solicitud
        """
        request = await self.get_request_by_id(request_id)
        if not request or request["status"] not in {"pending", "deferred"}:
            return False
        
        await self.update_status(request_id, "deferred")
        return True
    
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

