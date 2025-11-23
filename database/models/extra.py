"""
Modelos para módulos extras y preguntas de test.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, IDMixin, TimestampMixin


class ExtraModule(Base, IDMixin, TimestampMixin):
    """
    Modelo para módulos extras activados por doctor.
    """
    __tablename__ = 'extra_modules'
    
    doctor_id = Column(Integer, ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    module_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relaciones
    doctor = relationship("Doctor", back_populates="extra_modules")
    
    # Constraint único
    __table_args__ = (
        UniqueConstraint('doctor_id', 'module_name', name='uq_doctor_module'),
    )
    
    def __repr__(self):
        return f"<ExtraModule(id={self.id}, doctor_id={self.doctor_id}, module_name='{self.module_name}', is_active={self.is_active})>"


class TestQuestion(Base, IDMixin):
    """
    Modelo para preguntas del test de endometriosis.
    """
    __tablename__ = 'test_questions'
    
    bot_id = Column(Integer, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False)
    question = Column(String, nullable=False)
    display_order = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<TestQuestion(id={self.id}, bot_id={self.bot_id}, question='{self.question[:30]}...')>"

