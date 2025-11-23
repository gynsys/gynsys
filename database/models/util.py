"""
Modelos para tablas de utilidades (bot_logos, user_actions).
"""
from sqlalchemy import Column, Integer, String, PrimaryKeyConstraint
from .base import Base


class BotLogo(Base):
    """
    Modelo para logos de bots.
    """
    __tablename__ = 'bot_logos'
    
    bot_id = Column(Integer, primary_key=True)
    logo_header_1 = Column(String, nullable=True)
    logo_header_2 = Column(String, nullable=True)
    logo_signature = Column(String, nullable=True)
    
    def __repr__(self):
        return f"<BotLogo(bot_id={self.bot_id})>"


class UserAction(Base):
    """
    Modelo para acciones de usuarios (logs).
    """
    __tablename__ = 'user_actions'
    
    user_id = Column(Integer, nullable=False)
    bot_id = Column(Integer, nullable=False)
    action_key = Column(String, nullable=False)
    timestamp = Column(Integer, nullable=False)
    
    __table_args__ = (
        PrimaryKeyConstraint('user_id', 'bot_id', 'action_key'),
    )
    
    def __repr__(self):
        return f"<UserAction(user_id={self.user_id}, bot_id={self.bot_id}, action_key='{self.action_key}')>"

