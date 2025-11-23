"""
Servicios: Lógica de negocio pura (sin Telegram)
"""
from .formula_calculator import calculate_ho_formula
from .history_saver import build_history_data

__all__ = ['calculate_ho_formula', 'build_history_data']

