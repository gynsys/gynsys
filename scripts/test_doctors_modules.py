"""
Script de prueba para verificar la obtención de doctores y sus módulos
"""
import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.session import get_session
from database.engine import init_engine, close_engine
from features.admin.services.admin_service import AdminService
from database import extra_modules_db


async def test_get_doctors():
    """Prueba la obtención de doctores"""
    print("=" * 60)
    print("🧪 PRUEBA: Obtención de Doctores")
    print("=" * 60)
    
    # Inicializar engine
    await init_engine()
    
    try:
        admin_service = AdminService()
        
        # Obtener doctores activos
        print("\n📋 Doctores Activos:")
        print("-" * 60)
        active_doctors = await admin_service.get_all_doctors()
        print(f"Total: {len(active_doctors)} doctores activos")
        for doctor in active_doctors:
            print(f"  • ID: {doctor[0]}, Nombre: {doctor[1]}, Telegram ID: {doctor[2]}, Activo: {doctor[3]}")
        
        # Obtener doctores inactivos
        print("\n📋 Doctores Inactivos:")
        print("-" * 60)
        inactive_doctors = await admin_service.get_inactive_doctors()
        print(f"Total: {len(inactive_doctors)} doctores inactivos")
        for doctor in inactive_doctors:
            print(f"  • ID: {doctor[0]}, Nombre: {doctor[1]}, Telegram ID: {doctor[2]}, Activo: {doctor[3]}")
        
        # Combinar todos (excepto SuperAdmin)
        all_doctors = [d for d in active_doctors if d[0] != 1] + [d for d in inactive_doctors if d[0] != 1]
        print(f"\n📊 Total de doctores (sin SuperAdmin): {len(all_doctors)}")
        
        # Probar obtención de módulos para cada doctor
        print("\n" + "=" * 60)
        print("🧪 PRUEBA: Módulos por Doctor")
        print("=" * 60)
        
        for doctor in all_doctors[:5]:  # Solo los primeros 5 para no saturar
            doctor_id = doctor[0]
            doctor_name = doctor[1]
            active_modules = await extra_modules_db.get_active_modules_for_doctor(doctor_id)
            print(f"\n👨‍⚕️ {doctor_name} (ID: {doctor_id}):")
            if active_modules:
                print(f"   Módulos activos: {', '.join(active_modules)}")
            else:
                print("   Sin módulos activos")
        
        # Probar get_all_doctors_with_modules del repositorio
        print("\n" + "=" * 60)
        print("🧪 PRUEBA: get_all_doctors_with_modules()")
        print("=" * 60)
        
        async with get_session() as session:
            from database.repositories.extra_module_repository import ExtraModuleRepository
            repo = ExtraModuleRepository(session)
            doctors_with_modules = await repo.get_all_doctors_with_modules()
            
            print(f"Total devuelto: {len(doctors_with_modules)} doctores")
            for doctor_data in doctors_with_modules:
                print(f"  • {doctor_data['name']} (ID: {doctor_data['doctor_id']}): {len(doctor_data['modules'])} módulos")
                if doctor_data['modules']:
                    print(f"    Módulos: {', '.join(doctor_data['modules'])}")
        
        print("\n" + "=" * 60)
        print("✅ Pruebas completadas")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_engine()


if __name__ == "__main__":
    asyncio.run(test_get_doctors())

