"""
Modelo para ubicaciones.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, IDMixin


class Location(Base, IDMixin):
    """
    Modelo para ubicaciones de los doctores.
    """
    __tablename__ = 'locations'
    
    bot_id = Column(Integer, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    address = Column(Text, nullable=False)
    schedule = Column(Text)
    Maps_url = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0)
    
    # Relaciones
    bot = relationship("Bot", back_populates="locations")
    
    def __repr__(self):
        return f"<Location(id={self.id}, bot_id={self.bot_id}, name='{self.name}')>"

