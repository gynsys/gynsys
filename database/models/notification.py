"""
Modelo para notificaciones.
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base, IDMixin


class Notification(Base, IDMixin):
    """
    Modelo para notificaciones del sistema.
    """
    __tablename__ = 'notifications'
    
    bot_id = Column(Integer, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, nullable=False)  # Telegram ID del usuario
    message = Column(String, nullable=True)
    notification_type = Column(String, nullable=True, default='info')
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    bot = relationship("Bot", backref="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, bot_id={self.bot_id}, type={self.notification_type})>"

