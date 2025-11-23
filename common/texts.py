# /common/texts.py
# Movimiento directo del antiguo 'ui/texts.py'
import os
from database import content_db
import json
from .helpers import escape_html # Actualizado el import
import logging

logger = logging.getLogger(__name__)

_texts = {}

def load_texts():
    """Carga los textos desde el archivo JSON a un diccionario en memoria."""
    global _texts
    # Construye la ruta al archivo JSON relativo a este archivo
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, 'texts.json')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            _texts = json.load(f)
        logger.info("Archivo de textos 'texts.json' cargado correctamente.")
    except FileNotFoundError:
        logger.error(f"¡CRÍTICO! El archivo de textos no se encontró en {file_path}")
        _texts = {}
    except json.JSONDecodeError as e:
        logger.error(f"¡CRÍTICO! Error de formato en 'texts.json': {e}")
        _texts = {}

def get_text(key: str, default: str = None) -> str:
    """
    Obtiene un texto usando una clave con puntos (ej: 'preconsulta.ask_full_name').
    Si no se encuentra, devuelve la clave misma o un valor por defecto.
    """
    try:
        keys = key.split('.')
        value = _texts
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        logger.warning(f"Clave de texto no encontrada: '{key}'")
        return default if default is not None else key

# Carga los textos una vez al iniciar el bot
load_texts()

async def get_texto(key: str, bot_id: int, default: str = "Texto no encontrado.") -> str:
    text = await content_db.get_content(key, bot_id)
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"get_texto: key={key}, bot_id={bot_id}, text={'None' if text is None else text[:50] + '...' if len(text) > 50 else text}")
    return text if text is not None else default

async def get_mensaje_bienvenida(nombre_usuario: str, bot_id: int) -> str:
    """
    Obtiene el mensaje de bienvenida personalizado.
    IMPORTANTE: Solo devuelve UN mensaje completo (saludo + contenido editable).
    Si no hay contenido personalizado, usa el mensaje por defecto.
    """
    plantilla_inicio = f"💖 Hola, <b>{escape_html(nombre_usuario)}</b> 💖\n"
    
    # Obtener contenido personalizado directamente desde la BD (sin default)
    contenido_editable = await content_db.get_content("msg_bienvenida_editable", bot_id)
    
    # Si no hay contenido personalizado, usar el mensaje por defecto
    if contenido_editable is None:
        contenido_editable = "Bienvenido/a a mi consulta."
        logger.info(f"get_mensaje_bienvenida: bot_id={bot_id}, usando mensaje por defecto")
    else:
        logger.info(f"get_mensaje_bienvenida: bot_id={bot_id}, usando contenido personalizado: '{contenido_editable[:50]}...'")
    
    # Construir mensaje completo (solo UNA vez)
    # IMPORTANTE: Asegurar que no se concatene el mensaje por defecto si ya hay contenido personalizado
    # mensaje_completo = plantilla_inicio + contenido_editable
    mensaje_completo = contenido_editable
    # Verificación adicional: si el contenido personalizado contiene el mensaje por defecto, eliminarlo
    if contenido_editable and "Bienvenido/a a mi consulta." in contenido_editable and len(contenido_editable) > len("Bienvenido/a a mi consulta."):
        # El contenido personalizado contiene el mensaje por defecto, eliminarlo
        contenido_editable = contenido_editable.replace("Bienvenido/a a mi consulta.", "").strip()
        mensaje_completo = plantilla_inicio + contenido_editable
        logger.warning(f"⚠️ Se detectó mensaje por defecto en contenido personalizado, eliminado")
    
    logger.info(f"get_mensaje_bienvenida: mensaje_completo_length={len(mensaje_completo)}")
    logger.info(f"get_mensaje_bienvenida: mensaje_completo (primeros 100 chars): {mensaje_completo[:100]}...")
    return mensaje_completo

async def get_preguntas_test(bot_id: int) -> list:
    questions_json = await get_texto("test_questions", bot_id, "[]")
    try:
        return json.loads(questions_json)
    except json.JSONDecodeError:
        return []

def get_resultado_test(score: int, total_questions: int) -> str:
    if total_questions == 0:
        return "No se pudo calcular el resultado."
    
    porcentaje = (score / total_questions) * 100
    
    if porcentaje >= 70:
        nivel, recomendacion = "ALTA COINCIDENCIA", "Es crucial que busques una <b>evaluación especializada</b>."
    elif porcentaje >= 40:
        nivel, recomendacion = "MODERADA COINCIDENCIA", "Considera una <b>consulta ginecológica</b> para recibir orientación."
    else:
        nivel, recomendacion = "BAJA COINCIDENCIA", "Si tienes molestias, habla con un médico para explorar otras causas."
    
    return (f"Tu puntuación es de <b>{score}/{total_questions}</b> ({porcentaje:.0f}%).\n\n"
            f"Existe una <b>{nivel}</b> con los síntomas. {recomendacion}")

