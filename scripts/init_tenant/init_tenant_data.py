"""
Script para inicializar datos por defecto para un nuevo inquilino (tenant).
Lee el archivo tenant_defaults.json y carga los datos en la base de datos.
"""
import json
import asyncio
import aiosqlite
import logging
from pathlib import Path
import sys

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parents[2]))

from config import DB_PATH
from database import content_db, locations_db
from database import extra_modules_db
from database.content_db import add_item

logger = logging.getLogger(__name__)

# Ruta al archivo JSON de datos por defecto
DEFAULTS_FILE = Path(__file__).parent / "tenant_defaults.json"


async def init_tenant_data(bot_id: int, doctor_name: str = None):
    """
    Inicializa los datos por defecto para un nuevo inquilino.
    
    Args:
        bot_id: ID del bot (tenant) para el cual cargar los datos
        doctor_name: Nombre del doctor (opcional, para personalizar mensajes)
    
    Returns:
        bool: True si se cargaron los datos correctamente, False en caso contrario
    """
    try:
        # Leer el archivo JSON
        with open(DEFAULTS_FILE, 'r', encoding='utf-8') as f:
            defaults = json.load(f)
        
        logger.info(f"📋 Inicializando datos por defecto para bot_id={bot_id}")
        
        # 1. Cargar FAQs
        if 'faqs' in defaults:
            await _load_faqs(bot_id, defaults['faqs'])
            logger.info(f"✅ FAQs cargadas: {len(defaults['faqs'])}")
        
        # 2. Cargar Ubicaciones
        if 'locations' in defaults:
            await _load_locations(bot_id, defaults['locations'])
            logger.info(f"✅ Ubicaciones cargadas: {len(defaults['locations'])}")
        
        # 3. Cargar Información de Contacto
        if 'contact_info' in defaults:
            await _load_contact_info(bot_id, defaults['contact_info'])
            logger.info(f"✅ Información de contacto cargada")
        
        # 4. Cargar Precios
        if 'prices' in defaults:
            await _load_prices(bot_id, defaults['prices'])
            logger.info(f"✅ Precios cargados: {len(defaults['prices'])}")
        
        # 5. Cargar Galería
        if 'gallery' in defaults:
            await _load_gallery(bot_id, defaults['gallery'])
            logger.info(f"✅ Galería cargada: {len(defaults['gallery'])}")
        
        # 6. Cargar Configuración PDF
        if 'pdf_settings' in defaults:
            await _load_pdf_settings(bot_id, defaults['pdf_settings'], doctor_name)
            logger.info(f"✅ Configuración PDF cargada")
        
        # 7. Activar Módulos Extra
        if 'extra_modules' in defaults and 'default_active' in defaults['extra_modules']:
            await _activate_extra_modules(bot_id, defaults['extra_modules']['default_active'])
            logger.info(f"✅ Módulos extra activados: {defaults['extra_modules']['default_active']}")
        
        # 8. Cargar Mensaje de Bienvenida
        if 'welcome_message' in defaults:
            await _load_welcome_message(bot_id, defaults['welcome_message']['text'])
            logger.info(f"✅ Mensaje de bienvenida cargado")
        
        logger.info(f"✅ Datos por defecto inicializados correctamente para bot_id={bot_id}")
        return True
        
    except FileNotFoundError:
        logger.error(f"❌ No se encontró el archivo {DEFAULTS_FILE}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"❌ Error al parsear JSON: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error al inicializar datos: {e}", exc_info=True)
        return False


async def _load_faqs(bot_id: int, faqs: list):
    """Carga las FAQs por defecto"""
    conn = await aiosqlite.connect(DB_PATH)
    try:
        for faq in faqs:
            await conn.execute(
                "INSERT INTO faqs (bot_id, question, answer, display_order) VALUES (?, ?, ?, ?)",
                (bot_id, faq['question'], faq['answer'], faq.get('display_order', 0))
            )
        await conn.commit()
    finally:
        await conn.close()


async def _load_locations(bot_id: int, locations: list):
    """Carga las ubicaciones por defecto"""
    for location in locations:
        await locations_db.add_location(
            bot_id=bot_id,
            name=location['name'],
            address=location['address'],
            schedule=location.get('schedule', ''),
            gmaps_url=location.get('maps_url', '')
        )
        # Actualizar is_active si está especificado
        if 'is_active' in location:
            conn = await aiosqlite.connect(DB_PATH)
            try:
                await conn.execute(
                    "UPDATE locations SET is_active = ? WHERE bot_id = ? AND name = ?",
                    (1 if location['is_active'] else 0, bot_id, location['name'])
                )
                await conn.commit()
            finally:
                await conn.close()


async def _load_contact_info(bot_id: int, contact_info: dict):
    """Carga la información de contacto por defecto"""
    if 'header' in contact_info:
        await content_db.update_content("header_contacto", contact_info['header'], bot_id)
    if 'description' in contact_info:
        await content_db.update_content("description_contacto", contact_info['description'], bot_id)


async def _load_prices(bot_id: int, prices: list):
    """Carga los precios por defecto"""
    for price in prices:
        await add_item(
            bot_id=bot_id,
            table_name="precios",
            title=price['title'],
            content=price.get('content'),
            title_column="title",
            content_column="content"
        )


async def _load_gallery(bot_id: int, gallery: list):
    """Carga la galería por defecto"""
    for item in gallery:
        await add_item(
            bot_id=bot_id,
            table_name="gallery",
            title=item['title'],
            content=item.get('content'),
            title_column="title",
            content_column="content"
        )


async def _load_pdf_settings(bot_id: int, pdf_settings: dict, doctor_name: str = None):
    """Carga la configuración PDF por defecto"""
    conn = await aiosqlite.connect(DB_PATH)
    try:
        # Obtener doctor_id desde bot_id (igual que en _activate_extra_modules)
        cursor = await conn.execute(
            "SELECT admin_user_id FROM bots WHERE id = ?",
            (bot_id,)
        )
        result = await cursor.fetchone()
        if not result:
            logger.warning(f"No se encontró bot_id={bot_id} para cargar PDF settings")
            return
        
        admin_user_id = result[0]
        # Obtener doctor_id desde telegram_id
        cursor = await conn.execute(
            "SELECT id FROM doctors WHERE telegram_id = ?",
            (admin_user_id,)
        )
        doctor_result = await cursor.fetchone()
        if not doctor_result:
            logger.warning(f"No se encontró doctor para telegram_id={admin_user_id}")
            return
        
        doctor_id = doctor_result[0]
        
        # Personalizar doctor_name si se proporciona
        doctor_name_value = doctor_name if doctor_name else pdf_settings.get('doctor_name', 'Tu Nombre')
        
        # Verificar si ya existe configuración para este doctor_id
        cursor = await conn.execute("SELECT doctor_id FROM pdf_settings WHERE doctor_id = ?", (doctor_id,))
        exists = await cursor.fetchone()
        
        if not exists:
            # Insertar configuración por defecto
            await conn.execute("""
                INSERT INTO pdf_settings (
                    doctor_id, clinic_name, doctor_name, clinic_address, 
                    clinic_phone, clinic_email, show_logo, show_signature, footer_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doctor_id,  # Usar doctor_id, no bot_id
                pdf_settings.get('clinic_name', 'Nombre de tu Consultorio'),
                doctor_name_value,
                pdf_settings.get('clinic_address', 'Dirección de tu consultorio'),
                pdf_settings.get('clinic_phone', 'Teléfono de contacto'),
                pdf_settings.get('clinic_email', 'correo@ejemplo.com'),
                1 if pdf_settings.get('show_logo', True) else 0,
                1 if pdf_settings.get('show_signature', True) else 0,
                pdf_settings.get('footer_text', 'Información confidencial - Solo uso médico')
            ))
            await conn.commit()
    finally:
        await conn.close()


async def _activate_extra_modules(bot_id: int, modules: list):
    """Activa los módulos extra por defecto"""
    # Obtener el doctor_id desde bot_id
    conn = await aiosqlite.connect(DB_PATH)
    try:
        cursor = await conn.execute(
            "SELECT admin_user_id FROM bots WHERE id = ?",
            (bot_id,)
        )
        result = await cursor.fetchone()
        if result:
            admin_user_id = result[0]
            # Obtener doctor_id desde telegram_id
            cursor = await conn.execute(
                "SELECT id FROM doctors WHERE telegram_id = ?",
                (admin_user_id,)
            )
            doctor_result = await cursor.fetchone()
            if doctor_result:
                doctor_id = doctor_result[0]
                # Activar cada módulo directamente
                for module in modules:
                    await extra_modules_db.activate_module_for_doctor(doctor_id, module)
    finally:
        await conn.close()


async def _load_welcome_message(bot_id: int, welcome_text: str):
    """
    Carga el mensaje de bienvenida por defecto.
    IMPORTANTE: Usa update_content que elimina el mensaje viejo antes de insertar el nuevo,
    evitando duplicados.
    """
    # Usar update_content que ya maneja la eliminación de duplicados
    await content_db.update_content("msg_bienvenida_editable", welcome_text, bot_id)
    logger.info(f"✅ Mensaje de bienvenida cargado para bot_id={bot_id}: '{welcome_text[:50]}...'")


# Función para ejecutar desde línea de comandos
async def main():
    """Función principal para ejecutar el script desde línea de comandos"""
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python init_tenant_data.py <bot_id> [doctor_name]")
        print("Ejemplo: python init_tenant_data.py 2 'Dr. María'")
        sys.exit(1)
    
    bot_id = int(sys.argv[1])
    doctor_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = await init_tenant_data(bot_id, doctor_name)
    if success:
        print(f"✅ Datos inicializados correctamente para bot_id={bot_id}")
    else:
        print(f"❌ Error al inicializar datos para bot_id={bot_id}")
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

