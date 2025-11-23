"""
Lógica pura para calcular fórmulas obstétricas (G P A C).
Sin dependencias de Telegram, solo lógica de negocio.
"""
import logging

logger = logging.getLogger(__name__)


def calculate_ho_formula(user_data: dict) -> str:
    """
    Calcula la fórmula HO (G P A C) a partir de los datos del usuario.
    
    Args:
        user_data: Diccionario con los datos del usuario
    
    Returns:
        str: Fórmula HO formateada (ej: "G2 P1 A0 C1. Hijos vivos: 1.")
    """
    ho_results = user_data.get('ho_table_results', {})
    birth_details = user_data.get('birth_details', [])

    single_pregnancies = ho_results.get('single_pregnancies', 0)
    multiple_pregnancies = ho_results.get('multiple_pregnancies', 0)
    abortions = ho_results.get('abortions', 0)

    # Calcular Gravidez (G)
    gravidez = single_pregnancies + multiple_pregnancies + abortions
    if user_data.get('consultation_type') == 'Prenatal':
        gravidez += 1

    # Calcular Partos (P)
    partos = single_pregnancies + multiple_pregnancies

    # Calcular Cesáreas (C) y Hijos Vivos
    cesareas = sum(1 for birth in birth_details if birth.get('resolution', '').lower() == 'cesárea')
    hijos_vivos = sum(1 for birth in birth_details if birth.get('condition', '').lower() == 'vivo')

    # Manejo de caso especial: Prenatal primeriza
    if user_data.get('is_prenatal_flow') and user_data.get('is_first_pregnancy'):
        gravidez, partos, abortions, cesareas, hijos_vivos = 1, 0, 0, 0, 0

    ho_formula = f"G{gravidez} P{partos} A{abortions} C{cesareas}"
    ho_summary = f"{ho_formula}. Hijos vivos: {hijos_vivos}."

    logger.info(f"Fórmula HO calculada: {ho_summary}")
    return ho_summary


def calculate_ho_from_table(user_data: dict) -> str:
    """
    Calcula la fórmula HO desde los datos de la tabla (versión alternativa).
    Similar a calculate_ho_formula pero con lógica específica para tablas.
    
    Args:
        user_data: Diccionario con los datos del usuario
    
    Returns:
        str: Fórmula HO formateada
    """
    ho_results = user_data.get('ho_table_results', {})
    birth_details = user_data.get('birth_details', [])

    single_pregnancies = ho_results.get('single_pregnancies', 0)
    multiple_pregnancies = ho_results.get('multiple_pregnancies', 0)
    abortions = ho_results.get('abortions', 0)

    # Calcular Gravidez (G)
    gravidez = single_pregnancies + multiple_pregnancies + abortions
    if user_data.get('consultation_type') == 'Prenatal':
        gravidez += 1

    # Calcular Partos (P)
    partos = single_pregnancies + multiple_pregnancies

    # Calcular Cesáreas (C) y Hijos Vivos
    cesareas = sum(1 for birth in birth_details if birth.get('resolution', '').lower() == 'cesárea')
    hijos_vivos = sum(1 for birth in birth_details if birth.get('condition', '').lower() == 'vivo')

    # Lógica de fallback para prenatal primeriza
    if user_data.get('is_prenatal_flow') and user_data.get('is_first_pregnancy'):
        gravidez = 1
        partos = 0
        abortions = 0
        cesareas = 0
        hijos_vivos = 0

    ho_formula = f"G{gravidez} P{partos} A{abortions} C{cesareas}"
    ho_summary = f"{ho_formula}. Hijos vivos: {hijos_vivos}."

    logger.info(f"Fórmula HO calculada desde tabla: {ho_summary}")
    return ho_summary


def get_primigesta_formula() -> str:
    """Retorna la fórmula HO para primigesta."""
    return "G1 P0 A0 C0. Primigesta (embarazo actual)."


def get_nuligesta_formula() -> str:
    """Retorna la fórmula HO para nuligesta."""
    return "G0 P0 A0 C0. Nuligesta."

