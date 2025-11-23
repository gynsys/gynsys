# utils/encryption.py
"""
Módulo para cifrado y descifrado de datos sensibles usando Fernet (cryptography).

Este módulo proporciona funciones para cifrar datos antes de guardarlos en la base de datos
y descifrarlos cuando se recuperan, protegiendo información sensible de los pacientes.
"""

import logging
from cryptography.fernet import Fernet
from config import ENCRYPTION_KEY

logger = logging.getLogger(__name__)

# Inicializar el objeto Fernet con la clave de cifrado
try:
    if isinstance(ENCRYPTION_KEY, str):
        # Si la clave es un string, convertirla a bytes
        key_bytes = ENCRYPTION_KEY.encode('utf-8')
    else:
        key_bytes = ENCRYPTION_KEY
    
    cipher_suite = Fernet(key_bytes)
except Exception as e:
    logger.error(f"Error al inicializar el cifrado: {e}")
    cipher_suite = None


def encrypt_data(data: str) -> str | None:
    """
    Cifra un string usando Fernet.
    
    Args:
        data: String a cifrar. Si es None o vacío, retorna None.
        
    Returns:
        String cifrado en formato base64, o None si hay error o el dato es None/vacío.
    """
    if not cipher_suite:
        logger.error("El sistema de cifrado no está inicializado correctamente")
        return None
    
    if not data or not isinstance(data, str):
        # Si el dato es None o vacío, retornar None (no cifrar)
        return None
    
    try:
        # Convertir el string a bytes, cifrar y convertir a base64 string
        encrypted_bytes = cipher_suite.encrypt(data.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Error al cifrar datos: {e}")
        return None


def decrypt_data(encrypted_data: str) -> str | None:
    """
    Descifra un string cifrado con Fernet.
    
    Args:
        encrypted_data: String cifrado en formato base64, o None.
        
    Returns:
        String descifrado, o None si hay error, el dato es None, o no estaba cifrado.
    """
    if not cipher_suite:
        logger.error("El sistema de cifrado no está inicializado correctamente")
        return None
    
    if not encrypted_data or not isinstance(encrypted_data, str):
        # Si el dato es None o vacío, retornar None
        return None
    
    try:
        # Convertir el string base64 a bytes, descifrar y convertir a string
        decrypted_bytes = cipher_suite.decrypt(encrypted_data.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        # Si falla el descifrado, puede ser que el dato no esté cifrado (datos antiguos)
        logger.warning(f"Error al descifrar datos (puede ser dato antiguo sin cifrar): {e}")
        # Retornar el dato original si no se puede descifrar (compatibilidad con datos antiguos)
        return encrypted_data


def encrypt_dict_fields(data: dict, fields_to_encrypt: list[str]) -> dict:
    """
    Cifra campos específicos de un diccionario.
    
    Args:
        data: Diccionario con los datos.
        fields_to_encrypt: Lista de nombres de campos a cifrar.
        
    Returns:
        Diccionario con los campos especificados cifrados.
    """
    encrypted_data = data.copy()
    
    for field in fields_to_encrypt:
        if field in encrypted_data and encrypted_data[field] is not None:
            encrypted_value = encrypt_data(str(encrypted_data[field]))
            if encrypted_value is not None:
                encrypted_data[field] = encrypted_value
            # Si el cifrado falla, dejamos el valor original (pero se loguea el error)
    
    return encrypted_data


def decrypt_dict_fields(data: dict, fields_to_decrypt: list[str]) -> dict:
    """
    Descifra campos específicos de un diccionario.
    
    Args:
        data: Diccionario con los datos cifrados.
        fields_to_decrypt: Lista de nombres de campos a descifrar.
        
    Returns:
        Diccionario con los campos especificados descifrados.
    """
    decrypted_data = data.copy()
    
    for field in fields_to_decrypt:
        if field in decrypted_data and decrypted_data[field] is not None:
            decrypted_value = decrypt_data(str(decrypted_data[field]))
            if decrypted_value is not None:
                decrypted_data[field] = decrypted_value
            # Si el descifrado falla, se retorna el valor original (compatibilidad con datos antiguos)
    
    return decrypted_data

