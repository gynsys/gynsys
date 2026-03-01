"""
Repository para gestión de historiales médicos (preconsultas).
Reemplaza preconsulta_db.py con SQLAlchemy asíncrono.
Maneja encriptación automática de campos sensibles.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, text, and_
from sqlalchemy.orm import selectinload
from database.models.medical import MedicalHistory
from database.repositories.base_repository import BaseRepository
from database.sql_utils import validate_column_or_table_name
from utils.encryption import encrypt_dict_fields, decrypt_dict_fields
import logging

logger = logging.getLogger(__name__)

# Campos sensibles que deben ser cifrados antes de guardar en la base de datos
SENSITIVE_FIELDS = [
    'full_name', 'phone', 'ci', 'address',
    'family_history_mother', 'family_history_father', 'personal_history',
    'supplements', 'surgical_history',
    'gyn_menarche', 'gyn_ho', 'gyn_cycles', 'gyn_fertility_intent',
    'gyn_dysmenorrhea', 'gyn_sexarche', 'sexually_active',
    'gyn_fum', 'gyn_mac', 'gyn_previous_checkups', 'gyn_last_pap_smear',
    'leg_pain_type', 'leg_pain_zone',
    'sexual_pain_dyspareunia', 'sexual_pain_type', 'sexual_pain_scale',
    'habits_smoking', 'habits_alcohol',
    'gastro_symptoms_before_period', 'gastro_symptoms_during_period',
    'bowel_dischezia', 'bowel_dischezia_scale', 'bowel_frequency',
    'habits_urinary', 'urinary_pain_scale', 'urinary_irritation',
    'urinary_incontinence', 'urinary_nocturia',
    'functional_dispareunia', 'functional_leg_pain',
    'functional_gastro_before', 'functional_gastro_during',
    'functional_dischezia', 'functional_bowel_freq',
    'functional_urinary_problem', 'functional_urinary_pain',
    'functional_urinary_irritation', 'functional_urinary_incontinence',
    'functional_urinary_nocturia',
    'habits_physical_activity', 'habits_substance_use',
    'summary_functional_exam', 'summary_gyn_obstetric', 'summary_habits',
    'reason_for_visit', 'prenatal_details',
    'admin_physical_exam', 'admin_ultrasound', 'admin_diagnosis',
    'admin_plan', 'admin_observations'
]


class MedicalRepository(BaseRepository[MedicalHistory]):
    """
    Repository para operaciones con historiales médicos.
    Maneja encriptación automática de campos sensibles.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(MedicalHistory, session)
    
    async def save_history(self, data: dict) -> Optional[int]:
        """
        Guarda un nuevo registro de historia médica en la base de datos.
        Cifra campos sensibles antes de guardar.
        
        Args:
            data: Diccionario con los datos de la historia médica
        
        Returns:
            ID del nuevo registro o None si falla
        """
        try:
            # Validar que todos los nombres de columnas sean seguros
            column_names = list(data.keys())
            for col in column_names:
                if not validate_column_or_table_name(col):
                    logger.error(f"Nombre de columna inválido detectado: {col}")
                    return None
            
            # CIFRAR campos sensibles antes de guardar
            data_to_save = encrypt_dict_fields(data, SENSITIVE_FIELDS)
            
            # Crear instancia del modelo
            history = MedicalHistory(**data_to_save)
            self.session.add(history)
            await self.session.flush()
            await self.session.refresh(history)
            
            new_id = history.id
            logger.info(f"Nueva historia médica guardada con ID: {new_id} para el usuario {data.get('user_id')}")
            return new_id
            
        except Exception as e:
            logger.error(f"Error al guardar la historia médica en la base de datos: {e}", exc_info=True)
            await self.session.rollback()
            return None
    
    async def get_history_details(self, history_id: int, doctor_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene todos los detalles de una historia médica específica por su ID.
        Descifra campos sensibles después de leer.
        
        Args:
            history_id: ID de la historia
            doctor_id: ID del doctor
        
        Returns:
            Diccionario con todos los detalles descifrados, o None si no existe
        """
        result = await self.session.execute(
            select(MedicalHistory).where(
                MedicalHistory.id == history_id,
                MedicalHistory.doctor_id == doctor_id
            )
        )
        history = result.scalar_one_or_none()
        
        if not history:
            return None
        
        # Convertir a diccionario
        history_dict = {
            column.name: getattr(history, column.name)
            for column in history.__table__.columns
        }
        
        # DESCIFRAR campos sensibles antes de devolver
        history_dict = decrypt_dict_fields(history_dict, SENSITIVE_FIELDS)
        
        return history_dict
    
    async def complete_history(self, history_id: int, doctor_id: int, admin_data: dict) -> bool:
        """
        Actualiza una historia médica con los datos del admin y cambia el estado a 'completed'.
        Cifra campos sensibles antes de actualizar.
        
        Args:
            history_id: ID de la historia
            doctor_id: ID del doctor
            admin_data: Diccionario con los datos del admin a actualizar
        
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            # Validar nombres de columnas
            column_names = list(admin_data.keys())
            for col in column_names:
                if not validate_column_or_table_name(col):
                    logger.error(f"Nombre de columna inválido detectado: {col}")
                    return False
            
            # Añadir status
            admin_data['status'] = 'completed'
            
            # CIFRAR campos sensibles antes de actualizar
            admin_data_to_save = encrypt_dict_fields(admin_data, SENSITIVE_FIELDS)
            
            # Obtener la historia
            result = await self.session.execute(
                select(MedicalHistory).where(
                    MedicalHistory.id == history_id,
                    MedicalHistory.doctor_id == doctor_id
                )
            )
            history = result.scalar_one_or_none()
            
            if not history:
                return False
            
            # Actualizar campos
            for key, value in admin_data_to_save.items():
                if hasattr(history, key):
                    setattr(history, key, value)
            
            await self.session.flush()
            logger.info(f"Historia médica ID {history_id} completada y actualizada por el admin.")
            return True
            
        except Exception as e:
            logger.error(f"Error al completar la historia médica ID {history_id}: {e}", exc_info=True)
            await self.session.rollback()
            return False
    
    async def delete_history(self, history_id: int) -> bool:
        """
        Elimina un registro de historial médico por su ID.
        
        Args:
            history_id: ID de la historia
        
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        return await self.delete(history_id)
    
    async def get_latest_completed_histories(self, doctor_id: int, offset: int = 0, limit: int = 7) -> List[Dict[str, Any]]:
        """
        Obtiene los 'limit' historiales más recientes con estado 'completed'.
        Descifra el campo full_name después de leerlo.
        
        Args:
            doctor_id: ID del doctor
            limit: Límite de resultados
        
        Returns:
            Lista de diccionarios con historiales (full_name descifrado)
        """
        result = await self.session.execute(
            select(MedicalHistory)
            .where(
                MedicalHistory.doctor_id == doctor_id,
                MedicalHistory.status == 'completed'
            )
            .order_by(MedicalHistory.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        histories_objs = result.scalars().all()
        
        histories = []
        for history in histories_objs:
            history_dict = {
                'id': history.id,
                'user_id': history.user_id,
                'full_name': history.full_name,
                'visit_date': history.created_at.date().isoformat() if history.created_at else None
            }
            # Descifrar full_name
            if history_dict['full_name']:
                history_dict['full_name'] = decrypt_dict_fields(
                    {'full_name': history_dict['full_name']}, 
                    ['full_name']
                ).get('full_name')
            histories.append(history_dict)
        
        return histories

    async def get_completed_histories_count(self, doctor_id: int) -> int:
        """Obtiene la cantidad total de historiales completados para un doctor."""
        result = await self.session.execute(
            select(func.count())
            .where(
                MedicalHistory.doctor_id == doctor_id,
                MedicalHistory.status == 'completed'
            )
        )
        return result.scalar() or 0
    
    async def search_completed_histories_by_name(self, doctor_id: int, search_term: str) -> List[Dict[str, Any]]:
        """
        Busca pacientes por nombre entre los historiales con estado 'completed'.
        NOTA: Descifra todos los nombres y filtra en memoria (no ideal para grandes volúmenes).
        
        Args:
            doctor_id: ID del doctor
            search_term: Término de búsqueda
        
        Returns:
            Lista de pacientes únicos que coinciden
        """
        # Obtener todos los historiales completados
        result = await self.session.execute(
            select(MedicalHistory)
            .where(
                MedicalHistory.doctor_id == doctor_id,
                MedicalHistory.status == 'completed'
            )
            .order_by(MedicalHistory.created_at.desc())
        )
        histories = result.scalars().all()
        
        # Agrupar por user_id y full_name, mantener el más reciente
        patients_dict = {}
        for history in histories:
            key = (history.user_id, history.full_name)
            if key not in patients_dict:
                patients_dict[key] = history
        
        # Descifrar nombres y filtrar
        patients = []
        for history in patients_dict.values():
            if history.full_name:
                # Descifrar nombre
                decrypted_name = decrypt_dict_fields(
                    {'full_name': history.full_name}, 
                    ['full_name']
                ).get('full_name', '')
                
                # Filtrar por término de búsqueda
                if search_term.lower() in decrypted_name.lower():
                    patients.append({
                        'user_id': history.user_id,
                        'full_name': decrypted_name,
                        'last_visit': history.created_at.date().isoformat() if history.created_at else None
                    })
        
        # Ordenar por fecha más reciente
        patients.sort(key=lambda x: x['last_visit'] or '', reverse=True)
        
        return patients
    
    async def check_if_user_is_recurrent(self, user_id: int, doctor_id: int) -> Optional[Dict[str, Any]]:
        """
        Verifica si un usuario ya tiene un historial médico completo.
        
        Args:
            user_id: ID del usuario
            doctor_id: ID del doctor
        
        Returns:
            Diccionario con nombre y fecha del último historial, o None si es nuevo
        """
        result = await self.session.execute(
            select(MedicalHistory)
            .where(
                MedicalHistory.user_id == user_id,
                MedicalHistory.doctor_id == doctor_id,
                MedicalHistory.age.isnot(None)  # Tiene datos personales
            )
            .order_by(MedicalHistory.created_at.desc())
            .limit(1)
        )
        history = result.scalar_one_or_none()
        
        if not history:
            return None
        
        recurrent_info = {
            'full_name': history.full_name,
            'last_visit_date': history.created_at.date().isoformat() if history.created_at else None
        }
        
        # Descifrar full_name
        if recurrent_info['full_name']:
            recurrent_info['full_name'] = decrypt_dict_fields(
                {'full_name': recurrent_info['full_name']}, 
                ['full_name']
            ).get('full_name')
        
        return recurrent_info
    
    async def get_all_histories(self, doctor_id: int, offset: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene una lista paginada de todas las historias médicas pendientes.
        Descifra el campo full_name después de leerlo.
        
        Args:
            doctor_id: ID del doctor
            offset: Offset para paginación
            limit: Límite de resultados
        
        Returns:
            Lista de diccionarios con historiales (full_name descifrado)
        """
        result = await self.session.execute(
            select(
                MedicalHistory.id,
                MedicalHistory.full_name,
                MedicalHistory.created_at
            )
            .where(
                MedicalHistory.doctor_id == doctor_id,
                MedicalHistory.status == 'pending'
            )
            .order_by(MedicalHistory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = result.all()
        
        histories = []
        for row in rows:
            history_dict = {
                'id': row[0],
                'full_name': row[1],
                'created_at': row[2]
            }
            # Descifrar full_name
            if history_dict['full_name']:
                history_dict['full_name'] = decrypt_dict_fields(
                    {'full_name': history_dict['full_name']}, 
                    ['full_name']
                ).get('full_name')
            histories.append(history_dict)
        
        return histories
    
    async def get_patient_history_list(self, doctor_id: int, user_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de todos los informes completados para un paciente específico.
        Descifra el campo reason_for_visit después de leerlo.
        
        Args:
            doctor_id: ID del doctor
            user_id: ID del usuario
        
        Returns:
            Lista de diccionarios con historiales (consultation_type descifrado)
        """
        result = await self.session.execute(
            select(MedicalHistory)
            .where(
                MedicalHistory.doctor_id == doctor_id,
                MedicalHistory.user_id == user_id,
                MedicalHistory.status == 'completed'
            )
            .order_by(MedicalHistory.created_at.desc())
        )
        histories_objs = result.scalars().all()
        
        histories = []
        for history in histories_objs:
            history_dict = {
                'id': history.id,
                'visit_date': history.created_at.date().isoformat() if history.created_at else None,
                'consultation_type': history.reason_for_visit  # reason_for_visit como consultation_type
            }
            # Descifrar reason_for_visit
            if history_dict['consultation_type']:
                history_dict['consultation_type'] = decrypt_dict_fields(
                    {'reason_for_visit': history_dict['consultation_type']}, 
                    ['reason_for_visit']
                ).get('reason_for_visit', 'Consulta')
            histories.append(history_dict)
        
        return histories
    
    async def update_history_field(self, history_id: int, field: str, value: str) -> bool:
        """
        Actualiza un campo específico de un historial médico.
        Si el campo es sensible, lo cifra antes de actualizar.
        
        Args:
            history_id: ID de la historia
            field: Nombre del campo a actualizar
            value: Nuevo valor
        
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            # Validar nombre de columna
            if not validate_column_or_table_name(field):
                logger.error(f"Nombre de columna inválido detectado: {field}")
                return False
            
            # Obtener la historia
            history = await self.get_by_id(history_id)
            if not history:
                return False
            
            # Cifrar si es un campo sensible
            if field in SENSITIVE_FIELDS and value:
                from utils.encryption import encrypt_data
                encrypted_value = encrypt_data(str(value))
                if encrypted_value is not None:
                    value = encrypted_value
            
            # Actualizar campo
            setattr(history, field, value)
            await self.session.flush()
            return True
            
        except Exception as e:
            logger.error(f"Error al actualizar el campo '{field}' del historial {history_id}: {e}", exc_info=True)
            await self.session.rollback()
            return False
    
    async def get_next_history_number(self, doctor_id: int, consult_type: str) -> str:
        """
        Genera el siguiente número de historia correlativo en el formato T-YYYYMM-XXX.
        El correlativo se reinicia cada mes.
        T es 'G' para Ginecológica y 'P' para Prenatal.
        
        Args:
            doctor_id: ID del doctor
            consult_type: Tipo de consulta ("Ginecológica" o "Prenatal")
        
        Returns:
            Número de historia en formato T-YYYYMM-XXX
        """
        now = datetime.now()
        year_month_str = now.strftime("%Y%m")
        type_prefix = 'G' if consult_type == "Ginecológica" else 'P'
        search_prefix = f"{type_prefix}-{year_month_str}-"
        
        next_correlative = 1
        try:
            result = await self.session.execute(
                select(MedicalHistory.history_number)
                .where(
                    MedicalHistory.doctor_id == doctor_id,
                    MedicalHistory.history_number.like(f"{search_prefix}%")
                )
                .order_by(MedicalHistory.history_number.desc())
                .limit(1)
            )
            last_history = result.scalar_one_or_none()
            
            if last_history and last_history[0]:
                # Extraer el último correlativo
                last_correlative_str = last_history[0].split('-')[-1]
                next_correlative = int(last_correlative_str) + 1
                logger.info(f"Último NHM encontrado: {last_history[0]}. Siguiente correlativo: {next_correlative}")
            else:
                logger.info("No se encontraron NHM previos para este mes/tipo. Iniciando en 1.")
                
        except Exception as e:
            logger.error(f"Error al ejecutar la consulta para obtener el siguiente número de historia: {e}", exc_info=True)
            return f"ERROR-QUERY-{year_month_str}"
        
        # Formatear el nuevo número de historia completo
        new_history_number = f"{search_prefix}{str(next_correlative).zfill(3)}"
        return new_history_number
    
    async def save_history_number(self, history_id: int, history_number: str) -> bool:
        """
        Guarda el número de historia generado en un registro existente.
        
        Args:
            history_id: ID de la historia
            history_number: Número de historia a guardar
        
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            history = await self.get_by_id(history_id)
            if not history:
                return False
            
            history.history_number = history_number
            await self.session.flush()
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar el número de historia {history_number} para el ID {history_id}: {e}", exc_info=True)
            await self.session.rollback()
            return False

