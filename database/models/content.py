"""
Modelos para contenido dinámico: FAQs, Gallery, Precios, TextContent.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, IDMixin


class TextContent(Base):
    """
    Modelo para contenido de texto configurable por bot.
    Primary key compuesta: (key, bot_id)
    """
    __tablename__ = 'text_content'
    
    key = Column(String, primary_key=True, nullable=False)
    value = Column(Text, nullable=False)
    bot_id = Column(Integer, ForeignKey('bots.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    
    # Relaciones
    bot = relationship("Bot", back_populates="text_contents")
    
    def __repr__(self):
        return f"<TextContent(key='{self.key}', bot_id={self.bot_id})>"


class FAQ(Base, IDMixin):
    """
    Modelo para FAQs (preguntas frecuentes).
    """
    __tablename__ = 'faqs'
    
    bot_id = Column(Integer, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    display_order = Column(Integer, default=0)
    
    # Relaciones
    bot = relationship("Bot", back_populates="faqs")
    
    def __repr__(self):
        return f"<FAQ(id={self.id}, bot_id={self.bot_id}, question='{self.question[:30]}...')>"


class Gallery(Base, IDMixin):
    """
    Modelo para items de galería.
    """
    __tablename__ = 'gallery'
    
    bot_id = Column(Integer, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text)
    media_file_id = Column(String)
    media_type = Column(String)
    display_order = Column(Integer, default=0)
    
    # Relaciones
    bot = relationship("Bot", back_populates="gallery_items")
    
    def __repr__(self):
        return f"<Gallery(id={self.id}, bot_id={self.bot_id}, title='{self.title}')>"


class Precio(Base, IDMixin):
    """
    Modelo para precios.
    """
    __tablename__ = 'precios'
    
    bot_id = Column(Integer, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    display_order = Column(Integer, default=0)
    
    # Relaciones
    bot = relationship("Bot", back_populates="precios")
    
    def __repr__(self):
        return f"<Precio(id={self.id}, bot_id={self.bot_id}, title='{self.title}')>"

