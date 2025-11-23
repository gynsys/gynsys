"""
Modelo para historiales médicos (preconsultas).
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, IDMixin, TimestampMixin


class MedicalHistory(Base, IDMixin, TimestampMixin):
    """
    Modelo para historiales médicos completos.
    Nota: Los campos sensibles se cifran en el repository, no en el modelo.
    """
    __tablename__ = 'medical_histories'
    
    doctor_id = Column(Integer, ForeignKey('doctors.id', ondelete='CASCADE'), nullable=False)
    bot_id = Column(Integer)  # Mantener por compatibilidad durante migración
    user_id = Column(Integer, nullable=False)
    history_number = Column(String)
    
    # Información personal (cifrada en repository)
    full_name = Column(Text)
    age = Column(Text)
    ci = Column(Text)
    phone = Column(Text)
    address = Column(Text)
    occupation = Column(Text)
    
    # Antecedentes (cifrados en repository)
    family_history_mother = Column(Text)
    family_history_father = Column(Text)
    personal_history = Column(Text)
    supplements = Column(Text)
    surgical_history = Column(Text)
    
    # Ginecológicos (cifrados en repository)
    gyn_menarche = Column(Text)
    gyn_ho = Column(Text)
    gyn_cycles = Column(Text)
    gyn_fertility_intent = Column(Text)
    gyn_dysmenorrhea = Column(Text)
    gyn_sexarche = Column(Text)
    sexually_active = Column(Text)
    gyn_fum = Column(Text)
    gyn_mac = Column(Text)
    gyn_previous_checkups = Column(Text)
    gyn_last_pap_smear = Column(Text)
    
    # Funcionales (cifrados en repository)
    functional_dispareunia = Column(Text)
    functional_leg_pain = Column(Text)
    functional_gastro_before = Column(Text)
    functional_gastro_during = Column(Text)
    functional_dischezia = Column(Text)
    functional_bowel_freq = Column(Text)
    functional_urinary_problem = Column(Text)
    functional_urinary_pain = Column(Text)
    functional_urinary_irritation = Column(Text)
    functional_urinary_incontinence = Column(Text)
    functional_urinary_nocturia = Column(Text)
    
    # Hábitos (cifrados en repository)
    habits_physical_activity = Column(Text)
    habits_smoking = Column(Text)
    habits_alcohol = Column(Text)
    habits_substance_use = Column(Text)
    
    # Resúmenes (cifrados en repository)
    summary_functional_exam = Column(Text)
    summary_gyn_obstetric = Column(Text)
    summary_habits = Column(Text)
    
    # Consulta
    consultation_type = Column(Text)
    reason_for_visit = Column(Text)
    prenatal_details = Column(Text)  # JSON string
    
    # Datos del doctor
    admin_physical_exam = Column(Text)
    admin_ultrasound = Column(Text)
    admin_diagnosis = Column(Text)
    admin_plan = Column(Text)
    admin_observations = Column(Text)
    
    # Estado
    status = Column(String, default='pending', nullable=False)
    
    # Relaciones
    doctor = relationship("Doctor", back_populates="histories")
    
    def __repr__(self):
        return f"<MedicalHistory(id={self.id}, doctor_id={self.doctor_id}, user_id={self.user_id}, status='{self.status}')>"

