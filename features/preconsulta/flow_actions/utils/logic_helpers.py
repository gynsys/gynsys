"""
Helpers para lógica condicional.
Funciones puras para evaluar condiciones y cálculos.
"""
import logging

logger = logging.getLogger(__name__)


def process_conditional(user_data: dict, variable1: str, variable2: str, operator: str) -> bool:
    """
    Procesa una condición simple y devuelve True o False.
    
    Args:
        user_data: Diccionario con los datos del usuario
        variable1: Nombre de la primera variable
        variable2: Nombre de la segunda variable
        operator: Operador ('==', '!=', '>', '<', etc.)
    
    Returns:
        bool: True si la condición se cumple, False en caso contrario
    """
    var1_val = user_data.get(variable1)
    var2_val = user_data.get(variable2)

    # Intentar convertir a int si es posible
    try:
        var1_val = int(var1_val)
        var2_val = int(var2_val)
    except (ValueError, TypeError):
        pass

    if operator == '==':
        return var1_val == var2_val
    elif operator == '!=':
        return var1_val != var2_val
    elif operator == '>':
        return var1_val > var2_val
    elif operator == '<':
        return var1_val < var2_val
    elif operator == '>=':
        return var1_val >= var2_val
    elif operator == '<=':
        return var1_val <= var2_val
    else:
        logger.warning(f"Operador desconocido: {operator}, usando == por defecto")
        return var1_val == var2_val


def process_conditional_calc(user_data: dict, calc: str, variable: str, operator: str) -> bool:
    """
    Procesa una condición con cálculo y devuelve True o False.
    
    Args:
        user_data: Diccionario con los datos del usuario
        calc: Expresión de cálculo (ej: 'gyn_para + gyn_cesarean')
        variable: Variable a comparar
        operator: Operador de comparación
    
    Returns:
        bool: True si la condición se cumple, False en caso contrario
    """
    try:
        if calc == 'gyn_para + gyn_cesarean':
            val1 = int(user_data.get('gyn_para', 0))
            val2 = int(user_data.get('gyn_cesarean', 0))
            calc_result = val1 + val2
            var2_val = int(user_data.get(variable, 0))

            if operator == '==':
                return calc_result == var2_val
            elif operator == '!=':
                return calc_result != var2_val
            else:
                logger.warning(f"Operador no soportado para cálculo: {operator}")
                return False
        else:
            logger.error(f"Cálculo no implementado: {calc}")
            return False
    except (ValueError, TypeError) as e:
        logger.error(f"Error en el cálculo condicional: {e}")
        return False

