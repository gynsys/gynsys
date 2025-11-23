"""
Base declarativa y mixins para modelos SQLAlchemy.
"""
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import Column, Integer, DateTime


class Base(DeclarativeBase):
    """
    Base declarativa para todos los modelos.
    """
    pass


class TimestampMixin:
    """
    Mixin para agregar timestamps automáticos a los modelos.
    """
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)


class IDMixin:
    """
    Mixin para agregar ID primario a los modelos.
    """
    @declared_attr
    def id(cls):
        return Column(Integer, primary_key=True, autoincrement=True)

