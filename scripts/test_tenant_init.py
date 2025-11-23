"""
Script para probar la inicialización de datos de tenant
Úsalo para verificar que todo funciona correctamente
"""
import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_session
from database.repositories.user_repository import DoctorRepository
from database.models.bot import Bot
from sqlalchemy import select
from features.admin.services.admin_service import AdminService

async def test_tenant_init(telegram_id: int):
    """Prueba la inicialización de datos para un tenant"""
    print(f"🔍 Probando inicialización para telegram_id: {telegram_id}\n")
    
    admin_service = AdminService()
    
    # 1. Obtener bot_id
    print("1️⃣ Obteniendo bot_id...")
    bot_id = await admin_service.get_bot_id_for_doctor(telegram_id)
    if not bot_id:
        print("   ❌ No se encontró bot_id")
        return False
    print(f"   ✅ Bot_id encontrado: {bot_id}\n")
    
    # 2. Verificar que el archivo JSON existe
    print("2️⃣ Verificando archivo JSON...")
    json_file = Path(__file__).parent.parent / "scripts" / "init_tenant" / "tenant_defaults.json"
    if not json_file.exists():
        print(f"   ❌ Archivo no encontrado: {json_file}")
        return False
    print(f"   ✅ Archivo encontrado: {json_file}\n")
    
    # 3. Intentar inicializar
    print("3️⃣ Inicializando datos...")
    doctor_name = "Test Doctor"
    success = await admin_service.initialize_tenant_data(bot_id, doctor_name)
    
    if success:
        print("   ✅ Datos inicializados correctamente\n")
        
        # 4. Verificar que se cargaron los datos
        print("4️⃣ Verificando datos cargados...")
        async with get_session() as session:
            # Verificar FAQs
            from database.models.content import FAQ
            stmt = select(FAQ).where(FAQ.bot_id == bot_id)
            result = await session.execute(stmt)
            faqs = result.scalars().all()
            print(f"   📋 FAQs: {len(faqs)} encontradas")
            
            # Verificar Ubicaciones
            from database.models.location import Location
            stmt = select(Location).where(Location.bot_id == bot_id)
            result = await session.execute(stmt)
            locations = result.scalars().all()
            print(f"   📍 Ubicaciones: {len(locations)} encontradas")
            
            # Verificar Precios
            from database.models.content import Precio
            stmt = select(Precio).where(Precio.bot_id == bot_id)
            result = await session.execute(stmt)
            precios = result.scalars().all()
            print(f"   💰 Precios: {len(precios)} encontrados")
            
            # Verificar Galería
            from database.models.content import Gallery
            stmt = select(Gallery).where(Gallery.bot_id == bot_id)
            result = await session.execute(stmt)
            gallery = result.scalars().all()
            print(f"   🖼️  Galería: {len(gallery)} items encontrados")
        
        print("\n✅ Verificación completada")
        return True
    else:
        print("   ❌ Error al inicializar datos\n")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/test_tenant_init.py <telegram_id>")
        print("Ejemplo: python scripts/test_tenant_init.py 123456789")
        sys.exit(1)
    
    telegram_id = int(sys.argv[1])
    result = asyncio.run(test_tenant_init(telegram_id))
    sys.exit(0 if result else 1)

