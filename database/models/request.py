"""
Modelo para solicitudes de doctores.
"""
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from datetime import datetime
from .base import Base, IDMixin


class DoctorRequest(Base, IDMixin):
    """
    Modelo para solicitudes de registro de doctores.
    """
    __tablename__ = 'doctor_requests'
    
    full_name = Column(String, nullable=False)
    telegram_id = Column(Integer, nullable=False)
    status = Column(String, default='pending', nullable=False)
    doctor_id = Column(Integer, nullable=True)  # ID del doctor si fue aprobado
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Constraint único: un usuario solo puede tener una solicitud pendiente
    __table_args__ = (
        UniqueConstraint('telegram_id', 'status', name='uq_telegram_status'),
    )
    
    def __repr__(self):
        return f"<DoctorRequest(id={self.id}, telegram_id={self.telegram_id}, status='{self.status}')>"

