"""
Modelos relacionados con bots/tenants.
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, IDMixin


class Bot(Base, IDMixin):
    """
    Modelo para bots/tenants del sistema.
    Cada doctor tiene un bot asociado.
    """
    __tablename__ = 'bots'
    
    doctor_name = Column(String, nullable=False)
    token = Column(String, unique=True, nullable=False)
    admin_user_id = Column(Integer, nullable=False)  # Telegram ID del doctor
    is_active = Column(Boolean, default=True, nullable=False)
    
    logo_file_id = Column(String, nullable=True)
    logo_media_type = Column(String, nullable=True, default='photo')
    
    # Relaciones
    # Nota: La relación con Doctor se maneja por admin_user_id -> Doctor.telegram_id
    # No hay FK directo, se maneja en el repository
    text_contents = relationship("TextContent", back_populates="bot", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="bot", cascade="all, delete-orphan")
    faqs = relationship("FAQ", back_populates="bot", cascade="all, delete-orphan")
    gallery_items = relationship("Gallery", back_populates="bot", cascade="all, delete-orphan")
    precios = relationship("Precio", back_populates="bot", cascade="all, delete-orphan")
    user_tenants = relationship("UserTenant", back_populates="bot", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Bot(id={self.id}, doctor_name='{self.doctor_name}', admin_user_id={self.admin_user_id}, logo={self.logo_file_id})>"


class UserTenant(Base, IDMixin):
    """
    Modelo para asociación entre usuarios y tenants (bots).
    """
    __tablename__ = 'user_tenants'
    
    user_id = Column(Integer, nullable=False)  # Telegram ID del usuario
    bot_id = Column(Integer, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False)
    
    # Relaciones
    bot = relationship("Bot", back_populates="user_tenants")
    
    def __repr__(self):
        return f"<UserTenant(user_id={self.user_id}, bot_id={self.bot_id})>"

