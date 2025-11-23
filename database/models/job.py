"""
Modelo para la tabla citas (legacy) usada en jobs.
NOTA: Esta tabla es legacy y coexiste con appointments.
Se mantiene para compatibilidad con jobs_db.py.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from datetime import datetime
from .base import Base, IDMixin


class Cita(Base, IDMixin):
    """
    Modelo para la tabla legacy 'citas'.
    Esta tabla se usa para recordatorios y trabajos programados.
    """
    __tablename__ = 'citas'
    
    bot_id = Column(Integer, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, nullable=False)  # Telegram ID del usuario
    user_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    fecha = Column(String, nullable=False)  # Fecha como string (formato legacy)
    hora = Column(String, nullable=False)  # Hora como string (formato legacy)
    ubicacion = Column(String, nullable=False)
    status = Column(String, default='pending', nullable=False)
    reminder_sent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Cita(id={self.id}, user_id={self.user_id}, fecha='{self.fecha}', status='{self.status}')>"

