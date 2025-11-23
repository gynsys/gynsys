"""
Módulo de acciones de flujo de preconsulta.
Estructura organizada por capas:
- handlers/: Lógica de flujo (Telegram + Contexto)
- services/: Lógica de negocio pura
- router.py: Despachador de acciones
- utils/: Helpers para lógica condicional
"""
from .router import render

# Mantener compatibilidad hacia atrás
__all__ = ['render']

