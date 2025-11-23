"""
Modelo para configuración de PDF.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class PDFSetting(Base):
    """
    Modelo para configuración de PDF por doctor.
    Primary key compuesta: (doctor_id, setting_key)
    """
    __tablename__ = 'pdf_settings'
    
    doctor_id = Column(Integer, ForeignKey('doctors.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    setting_key = Column(String, primary_key=True, nullable=False)
    setting_value = Column(String)
    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    doctor = relationship("Doctor", back_populates="pdf_settings")
    
    def __repr__(self):
        return f"<PDFSetting(doctor_id={self.doctor_id}, setting_key='{self.setting_key}', value='{self.setting_value}')>"

