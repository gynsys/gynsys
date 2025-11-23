"""
Modelos para citas y slots de citas.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base, IDMixin


class Slot(Base, IDMixin):
    """
    Modelo para slots (cupos) de citas creados por el doctor.
    """
    __tablename__ = 'slots'
    
    doctor_id = Column(Integer, nullable=False)
    start_ts = Column(Integer, nullable=False)  # Timestamp Unix
    duration_min = Column(Integer, nullable=False)
    note = Column(Text)
    is_active = Column(Integer, default=1, nullable=False)  # SQLite usa INTEGER para boolean
    
    # Relaciones
    appointments = relationship("Appointment", back_populates="slot", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Slot(id={self.id}, doctor_id={self.doctor_id}, start_ts={self.start_ts})>"


class Appointment(Base, IDMixin):
    """
    Modelo para citas (reservas de pacientes sobre un slot).
    """
    __tablename__ = 'appointments'
    
    slot_id = Column(Integer, ForeignKey('slots.id', ondelete='CASCADE'), nullable=False, unique=True)
    doctor_id = Column(Integer, nullable=False)
    patient_telegram_id = Column(Integer, nullable=False)
    patient_name = Column(String)
    consultation_type = Column(String)
    reason = Column(Text)
    location = Column(String)
    status = Column(String, default='pending', nullable=False)
    booked_at = Column(Integer, nullable=False)  # Timestamp Unix
    
    # Relaciones
    slot = relationship("Slot", back_populates="appointments")
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, slot_id={self.slot_id}, patient_telegram_id={self.patient_telegram_id}, status='{self.status}')>"

