# database/sql_utils.py
"""
Utilidades para construir consultas SQL de forma segura.
Proporciona funciones helper para validar nombres de columnas y tablas.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Lista blanca de caracteres permitidos para nombres de columnas/tablas
ALLOWED_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

def validate_column_or_table_name(name: str) -> bool:
    """
    Valida que un nombre de columna o tabla sea seguro.
    
    Solo permite nombres que:
    - Empiecen con letra o guion bajo
    - Contengan solo letras, números y guiones bajos
    - No contengan espacios ni caracteres especiales
    
    Args:
        name: Nombre de columna o tabla a validar
        
    Returns:
        True si el nombre es válido, False en caso contrario
    """
    if not isinstance(name, str):
        return False
    return bool(ALLOWED_NAME_PATTERN.match(name))

def safe_column_list(columns: list[str]) -> str:
    """
    Construye una lista segura de columnas para usar en SQL.
    
    Valida cada columna antes de incluirla en la lista.
    
    Args:
        columns: Lista de nombres de columnas
        
    Returns:
        String con la lista de columnas separadas por comas
        
    Raises:
        ValueError: Si alguna columna no es válida
    """
    validated = []
    for col in columns:
        if not validate_column_or_table_name(col):
            raise ValueError(f"Nombre de columna inválido: {col}")
        validated.append(col)
    return ', '.join(validated)

def safe_table_name(table_name: str) -> str:
    """
    Valida y retorna un nombre de tabla seguro.
    
    Args:
        table_name: Nombre de la tabla
        
    Returns:
        El nombre de la tabla si es válido
        
    Raises:
        ValueError: Si el nombre de tabla no es válido
    """
    if not validate_column_or_table_name(table_name):
        raise ValueError(f"Nombre de tabla inválido: {table_name}")
    return table_name

def build_set_clause(columns: list[str]) -> str:
    """
    Construye la cláusula SET para un UPDATE de forma segura.
    
    Ejemplo: build_set_clause(['name', 'age']) -> "name = ?, age = ?"
    
    Args:
        columns: Lista de nombres de columnas a actualizar
        
    Returns:
        String con la cláusula SET
        
    Raises:
        ValueError: Si alguna columna no es válida
    """
    validated = safe_column_list(columns)
    return ', '.join([f"{col} = ?" for col in validated.split(', ')])

def build_insert_columns(columns: list[str]) -> tuple[str, str]:
    """
    Construye las listas de columnas y placeholders para un INSERT.
    
    Ejemplo: build_insert_columns(['name', 'age']) -> ("name, age", "?, ?")
    
    Args:
        columns: Lista de nombres de columnas
        
    Returns:
        Tupla con (lista_columnas, lista_placeholders)
        
    Raises:
        ValueError: Si alguna columna no es válida
    """
    validated = safe_column_list(columns)
    placeholders = ', '.join(['?' for _ in columns])
    return validated, placeholders

