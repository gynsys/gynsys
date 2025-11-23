"""
Repository para gestión de configuración de PDF.
Reemplaza features/pdf_configuration/database.py con SQLAlchemy asíncrono.
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from database.models.pdf import PDFSetting
from database.repositories.base_repository import BaseRepository
import logging

logger = logging.getLogger(__name__)

# Valores por defecto para cada doctor
DEFAULT_PDF_SETTINGS = {
    'doctor_name': {'value': 'Dra. Mariel Herrera', 'visible': True},
    'specialty': {'value': 'Especialista en Ginecología y Obstetricia', 'visible': True},
    'location': {'value': 'Caracas-Guarenas Guatire', 'visible': True},
    'phones': {'value': '04244281876-04127738918', 'visible': True},
    'mpps_number': {'value': '140.795', 'visible': True},
    'cmdm_number': {'value': '38.789', 'visible': True},
    'doctor_id': {'value': '23.812.988', 'visible': True},
    'report_title': {'value': 'INFORME MÉDICO', 'visible': True},
    'footer_city': {'value': 'Guarenas', 'visible': True},
    'logo_header_1': {'value': None, 'visible': True},
    'logo_header_2': {'value': None, 'visible': True},
    'logo_signature': {'value': None, 'visible': True},
    'include_functional_exam': {'value': '1', 'visible': True}  # 1 = incluido, 0 = excluido
}


class PDFRepository:
    """
    Repository para operaciones con configuración de PDF.
    Nota: PDFSetting tiene primary key compuesta, por lo que no hereda de BaseRepository.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_pdf_settings(self, doctor_id: int) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene TODA la configuración de PDF para un doctor específico.
        
        Args:
            doctor_id: ID del doctor
        
        Returns:
            Diccionario con todas las configuraciones (aplica defaults si faltan)
        """
        result = await self.session.execute(
            select(PDFSetting).where(PDFSetting.doctor_id == doctor_id)
        )
        settings_objs = result.scalars().all()
        
        settings = {}
        for setting in settings_objs:
            settings[setting.setting_key] = {
                'value': setting.setting_value,
                'visible': bool(setting.is_visible)
            }
        
        # Aplicar valores por defecto para configuraciones faltantes
        return await self.apply_default_settings(doctor_id, settings)
    
    async def apply_default_settings(
        self, 
        doctor_id: int, 
        current_settings: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Aplica valores por defecto a configuraciones faltantes.
        
        Args:
            doctor_id: ID del doctor
            current_settings: Configuraciones actuales
        
        Returns:
            Diccionario con configuraciones completas (incluyendo defaults)
        """
        final_settings = current_settings.copy()
        
        for key, default_config in DEFAULT_PDF_SETTINGS.items():
            if key not in final_settings:
                final_settings[key] = default_config.copy()
                # Guardar el valor por defecto en la BD
                await self.update_pdf_setting(
                    doctor_id, 
                    key, 
                    default_config['value'], 
                    default_config['visible']
                )
        
        return final_settings
    
    async def update_pdf_setting(
        self, 
        doctor_id: int, 
        setting_key: str, 
        setting_value: Optional[str], 
        is_visible: bool = True
    ) -> bool:
        """
        Actualiza o crea una configuración de PDF para un doctor.
        
        Args:
            doctor_id: ID del doctor
            setting_key: Clave de la configuración
            setting_value: Valor de la configuración
            is_visible: Si es visible en el panel
        
        Returns:
            True si se actualizó correctamente
        """
        try:
            # Buscar si ya existe
            result = await self.session.execute(
                select(PDFSetting).where(
                    PDFSetting.doctor_id == doctor_id,
                    PDFSetting.setting_key == setting_key
                )
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Actualizar existente
                existing.setting_value = setting_value
                existing.is_visible = is_visible
            else:
                # Crear nuevo
                new_setting = PDFSetting(
                    doctor_id=doctor_id,
                    setting_key=setting_key,
                    setting_value=setting_value,
                    is_visible=is_visible
                )
                self.session.add(new_setting)
            
            await self.session.flush()
            logger.info(f"Configuración PDF actualizada - Doctor: {doctor_id}, Key: {setting_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando configuración PDF para doctor {doctor_id}: {e}", exc_info=True)
            await self.session.rollback()
            return False
    
    async def toggle_setting_visibility(self, doctor_id: int, setting_key: str) -> bool:
        """
        Alterna la visibilidad de una configuración.
        
        Args:
            doctor_id: ID del doctor
            setting_key: Clave de la configuración
        
        Returns:
            True si se alternó correctamente
        """
        try:
            result = await self.session.execute(
                select(PDFSetting).where(
                    PDFSetting.doctor_id == doctor_id,
                    PDFSetting.setting_key == setting_key
                )
            )
            setting = result.scalar_one_or_none()
            
            if setting:
                setting.is_visible = not setting.is_visible
                await self.session.flush()
                return True
            else:
                # Si no existe, crear con visibilidad True
                new_setting = PDFSetting(
                    doctor_id=doctor_id,
                    setting_key=setting_key,
                    setting_value=None,
                    is_visible=True
                )
                self.session.add(new_setting)
                await self.session.flush()
                return True
                
        except Exception as e:
            logger.error(f"Error alternando visibilidad para doctor {doctor_id}, key {setting_key}: {e}", exc_info=True)
            await self.session.rollback()
            return False
    
    async def get_setting_value(self, doctor_id: int, setting_key: str) -> str:
        """
        Obtiene el valor de una configuración específica.
        
        Args:
            doctor_id: ID del doctor
            setting_key: Clave de la configuración
        
        Returns:
            Valor de la configuración o valor por defecto
        """
        settings = await self.get_pdf_settings(doctor_id)
        return settings.get(setting_key, {}).get('value', DEFAULT_PDF_SETTINGS.get(setting_key, {}).get('value', ''))

