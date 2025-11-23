# common/pdf_generator.py
# Módulo de compatibilidad: Re-exporta las funciones desde common/pdf/
# Este archivo mantiene la compatibilidad con el código existente que importa desde pdf_generator

# Re-exportar todo desde el módulo pdf
from .pdf import (
    format_simple_antecedente,
    format_family_history,
    create_logo_image,
    create_qr_image,
    generate_medical_report,
    generate_summary_report,
    build_narrative_summary,
)

# Mantener compatibilidad: exportar todo lo que se esperaba antes
__all__ = [
    'format_simple_antecedente',
    'format_family_history',
    'create_logo_image',
    'create_qr_image',
    'generate_medical_report',
    'generate_summary_report',
    'build_narrative_summary',
]
