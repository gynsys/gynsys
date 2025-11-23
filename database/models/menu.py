"""
Modelos para menús y botones de menú.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, IDMixin


class MainMenuButton(Base, IDMixin):
    """
    Modelo para botones del menú principal.
    """
    __tablename__ = 'main_menu_buttons'
    
    bot_id = Column(Integer, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False)
    text = Column(String, nullable=False)
    callback_data = Column(String, nullable=False)
    row_number = Column(Integer, nullable=False)
    display_order = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relaciones
    bot = relationship("Bot", backref="main_menu_buttons")
    
    def __repr__(self):
        return f"<MainMenuButton(id={self.id}, text='{self.text}', bot_id={self.bot_id})>"


class Submenu(Base, IDMixin):
    """
    Modelo para submenús.
    """
    __tablename__ = 'submenus'
    
    bot_id = Column(Integer, ForeignKey('bots.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    
    # Relaciones
    bot = relationship("Bot", backref="submenus")
    buttons = relationship("SubmenuButton", back_populates="submenu", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Submenu(id={self.id}, name='{self.name}', bot_id={self.bot_id})>"


class SubmenuButton(Base, IDMixin):
    """
    Modelo para botones de submenús.
    """
    __tablename__ = 'submenu_buttons'
    
    submenu_id = Column(Integer, ForeignKey('submenus.id', ondelete='CASCADE'), nullable=False)
    text = Column(String, nullable=False)
    callback_data = Column(String, nullable=False)
    row_number = Column(Integer, nullable=False)
    display_order = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relaciones
    submenu = relationship("Submenu", back_populates="buttons")
    
    def __repr__(self):
        return f"<SubmenuButton(id={self.id}, text='{self.text}', submenu_id={self.submenu_id})>"

