"""
Script de prueba para verificar que la configuración de SQLAlchemy funciona correctamente.
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.engine import init_engine, close_engine
from database.session import get_session
from database.models import Doctor, Bot, MedicalHistory
from sqlalchemy import select


async def test_connection():
    """Prueba la conexión y operaciones básicas"""
    print("🔧 Inicializando engine...")
    await init_engine()
    
    try:
        print("✅ Engine inicializado correctamente")
        
        # Probar obtener una sesión
        print("\n📝 Probando obtener sesión...")
        async with get_session() as session:
            print("✅ Sesión obtenida correctamente")
            
            # Probar query simple
            print("\n🔍 Probando query simple...")
            result = await session.execute(select(Doctor).limit(1))
            doctors = result.scalars().all()
            print(f"✅ Query ejecutada. Doctores encontrados: {len(doctors)}")
            
            if doctors:
                print(f"   Primer doctor: {doctors[0]}")
            
            # Probar query de otra tabla
            print("\n🔍 Probando query de MedicalHistory...")
            result = await session.execute(select(MedicalHistory).limit(1))
            histories = result.scalars().all()
            print(f"✅ Query ejecutada. Historias encontradas: {len(histories)}")
            
            # Probar query de Bot
            print("\n🔍 Probando query de Bot...")
            result = await session.execute(select(Bot).limit(1))
            bots = result.scalars().all()
            print(f"✅ Query ejecutada. Bots encontrados: {len(bots)}")
            
            if bots:
                print(f"   Primer bot: {bots[0]}")
        
        print("\n✅ Todas las pruebas pasaron correctamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🔒 Cerrando engine...")
        await close_engine()
        print("✅ Engine cerrado correctamente")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBA DE CONFIGURACIÓN SQLALCHEMY")
    print("=" * 60)
    asyncio.run(test_connection())
    print("\n" + "=" * 60)

