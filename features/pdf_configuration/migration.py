# features/pdf_configuration/migration.py
import logging
from database.connection import get_db_connection
from .database import update_pdf_setting

logger = logging.getLogger(__name__)

async def migrate_existing_logos():
    """Migra logos desde bot_logos a pdf_settings para todos los bots"""
    conn = await get_db_connection()
    migrated_count = 0
    
    try:
        # Obtener todos los bots con logos existentes
        query = "SELECT bot_id, logo_header_1, logo_header_2, logo_signature FROM bot_logos"
        async with conn.execute(query) as cursor:
            bots_with_logos = await cursor.fetchall()
        
        for bot in bots_with_logos:
            bot_id = bot['bot_id']
            migrations = [
                ('logo_header_1', bot['logo_header_1']),
                ('logo_header_2', bot['logo_header_2']), 
                ('logo_signature', bot['logo_signature'])
            ]
            
            for key, value in migrations:
                if value:  # Solo migrar si existe valor
                    success = await update_pdf_setting(bot_id, key, value, True)
                    if success:
                        migrated_count += 1
                        logger.info(f"Migrado {key} para bot {bot_id}")
                    else:
                        logger.error(f"Error migrando {key} para bot {bot_id}")
                    
        logger.info(f"Migración completada: {migrated_count} logos migrados para {len(bots_with_logos)} bots")
        
    except Exception as e:
        logger.error(f"Error en migración de logos: {e}")
    finally:
        await conn.close()
    
    return migrated_count

async def initialize_bot_pdf_settings(bot_id: int):
    """Inicializa las configuraciones PDF para un nuevo bot"""
    from .database import DEFAULT_PDF_SETTINGS
    
    initialized_count = 0
    for key, default_config in DEFAULT_PDF_SETTINGS.items():
        success = await update_pdf_setting(
            bot_id, 
            key, 
            default_config['value'], 
            default_config['visible']
        )
        if success:
            initialized_count += 1
    
    logger.info(f"Configuración PDF inicializada para bot {bot_id}: {initialized_count} settings")
    return initialized_count