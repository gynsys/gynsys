"""
Script de prueba para verificar que ExtraModuleRepository funciona correctamente.
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.engine import init_engine, close_engine
from database.session import get_session
from database.repositories.extra_module_repository import ExtraModuleRepository
from database.models.user import Doctor


async def test_repository():
    """Prueba las operaciones del repository"""
    print("🔧 Inicializando engine...")
    await init_engine()
    
    try:
        print("✅ Engine inicializado correctamente\n")
        
        async with get_session() as session:
            repo = ExtraModuleRepository(session)
            
            # Obtener un doctor de prueba (o crear uno si no existe)
            from sqlalchemy import select
            result = await session.execute(
                select(Doctor).where(Doctor.is_active == True).limit(1)
            )
            doctor = result.scalar_one_or_none()
            
            if not doctor:
                print("⚠️ No se encontró ningún doctor activo para probar")
                return
            
            doctor_id = doctor.id
            print(f"📋 Probando con doctor ID: {doctor_id} ({doctor.name})\n")
            
            # 1. Obtener módulos activos
            print("1️⃣ Probando get_active_modules_for_doctor...")
            active_modules = await repo.get_active_modules_for_doctor(doctor_id)
            print(f"   ✅ Módulos activos: {active_modules}\n")
            
            # 2. Verificar si un módulo está activo
            print("2️⃣ Probando is_module_active_for_doctor...")
            is_test_active = await repo.is_module_active_for_doctor(doctor_id, 'test')
            print(f"   ✅ Módulo 'test' activo: {is_test_active}\n")
            
            # 3. Activar un módulo
            print("3️⃣ Probando activate_module_for_doctor...")
            activated = await repo.activate_module_for_doctor(doctor_id, 'test')
            print(f"   ✅ Módulo 'test' activado: {activated}\n")
            
            # 4. Verificar que está activo
            print("4️⃣ Verificando que el módulo está activo...")
            is_active = await repo.is_module_active_for_doctor(doctor_id, 'test')
            print(f"   ✅ Módulo 'test' activo: {is_active}\n")
            
            # 5. Desactivar el módulo
            print("5️⃣ Probando deactivate_module_for_doctor...")
            deactivated = await repo.deactivate_module_for_doctor(doctor_id, 'test')
            print(f"   ✅ Módulo 'test' desactivado: {deactivated}\n")
            
            # 6. Alternar el módulo
            print("6️⃣ Probando toggle_module_for_doctor...")
            toggled = await repo.toggle_module_for_doctor(doctor_id, 'test')
            print(f"   ✅ Módulo 'test' alternado: {toggled}\n")
            
            # 7. Obtener todos los doctores con módulos
            print("7️⃣ Probando get_all_doctors_with_modules...")
            doctors = await repo.get_all_doctors_with_modules()
            print(f"   ✅ Doctores encontrados: {len(doctors)}")
            for doc in doctors[:3]:  # Mostrar solo los primeros 3
                print(f"      - {doc['name']}: {doc['modules']}\n")
            
            # 8. Obtener módulos disponibles
            print("8️⃣ Probando get_available_modules...")
            available = await repo.get_available_modules()
            print(f"   ✅ Módulos disponibles: {len(available)}")
            for mod in available:
                print(f"      - {mod['name']}: {mod['display_name']}\n")
            
            # Commit manual (get_session hace commit automático, pero por si acaso)
            await session.commit()
        
        print("✅ Todas las pruebas pasaron correctamente!")
        
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
    print("🧪 PRUEBA DE EXTRA MODULE REPOSITORY")
    print("=" * 60)
    asyncio.run(test_repository())
    print("\n" + "=" * 60)

