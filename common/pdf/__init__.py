# common/pdf/__init__.py
# Módulo de generación de PDFs - Re-exporta todas las funciones públicas

from .utils import (
    format_simple_antecedente,
    format_family_history,
    create_logo_image,
    create_qr_image
)

from .medical_history import generate_medical_report
from .summary_report import generate_summary_report
from .summary_builder import build_narrative_summary

__all__ = [
    'format_simple_antecedente',
    'format_family_history',
    'create_logo_image',
    'create_qr_image',
    'generate_medical_report',
    'generate_summary_report',
    'build_narrative_summary',
]

