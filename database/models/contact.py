"""
Modelo para información de contacto de doctores.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime
from .base import Base, IDMixin


class ContactInfo(Base, IDMixin):
    """
    Modelo para información de contacto de doctores.
    Cada doctor tiene un único registro de contacto.
    """
    __tablename__ = 'contact_info'
    
    doctor_id = Column(Integer, ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False, unique=True)
    phone = Column(String, nullable=True)
    whatsapp = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    website = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relación con Doctor (opcional, se puede acceder desde el repository)
    
    def __repr__(self):
        return f"<ContactInfo(doctor_id={self.doctor_id}, phone={self.phone})>"

