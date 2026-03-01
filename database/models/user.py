"""
Modelos relacionados con usuarios: Doctores y asociaciones paciente-médico.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, IDMixin


class Doctor(Base, IDMixin, TimestampMixin):
    """
    Modelo para doctores/médicos del sistema.
    """
    __tablename__ = 'doctors'
    
    name = Column(String, nullable=False)
    telegram_id = Column(Integer, unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relaciones
    patients = relationship("PatientDoctor", back_populates="doctor", cascade="all, delete-orphan")
    histories = relationship("MedicalHistory", back_populates="doctor", cascade="all, delete-orphan")
    # Nota: La relación con Bot se maneja por admin_user_id -> telegram_id (no hay FK directo)
    extra_modules = relationship("ExtraModule", back_populates="doctor", cascade="all, delete-orphan")
    pdf_settings = relationship("PDFSetting", back_populates="doctor", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Doctor(id={self.id}, name='{self.name}', telegram_id={self.telegram_id}, is_active={self.is_active})>"


class PatientDoctor(Base, IDMixin):
    """
    Modelo para asociación entre pacientes y doctores.
    Nota: No usa TimestampMixin porque la tabla real solo tiene assigned_at.
    """
    __tablename__ = 'patient_doctor'
    
    patient_telegram_id = Column(Integer, nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    doctor = relationship("Doctor", back_populates="patients")
    
    # Constraint único
    __table_args__ = (
        UniqueConstraint('patient_telegram_id', 'doctor_id', name='uq_patient_doctor'),
    )
    
    def __repr__(self):
        return f"<PatientDoctor(patient_telegram_id={self.patient_telegram_id}, doctor_id={self.doctor_id})>"


class InstitutionUser(Base, IDMixin):
    """
    Modelo para co-usuarios/equipo de una institución o clínica.
    Permite que múltiples cuentas de Telegram operen un mismo bot/tenant.
    """
    __tablename__ = 'institution_users'
    
    # Telegram ID del co-usuario (Ej: Secretaria, Colega)
    telegram_id = Column(Integer, unique=True, nullable=False)
    
    # ID del Doctor (Tenant) propietario
    institution_id = Column(Integer, ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    
    # Nombre del colaborador para logs y mensajes
    name = Column(String, nullable=False)
    
    # Relación
    institution = relationship("Doctor", backref="institution_users")
    
    def __repr__(self):
        return f"<InstitutionUser(telegram_id={self.telegram_id}, institution_id={self.institution_id}, name='{self.name}')>"


