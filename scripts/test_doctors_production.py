"""
Script de prueba para verificar la obtención de doctores en producción
Ejecutar en el servidor para diagnosticar el problema
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
from database.repositories.user_repository import DoctorRepository
from sqlalchemy import select
from database.models.user import Doctor


async def test_get_doctors_production():
    """Prueba la obtención de doctores en producción"""
    print("=" * 60)
    print("🧪 PRUEBA: Obtención de Doctores (Producción)")
    print("=" * 60)
    
    # Inicializar engine
    await init_engine()
    
    try:
        # PRUEBA 1: Usando admin_service
        print("\n📋 PRUEBA 1: Usando AdminService.get_all_doctors()")
        print("-" * 60)
        admin_service = AdminService()
        active_doctors = await admin_service.get_all_doctors()
        print(f"Total: {len(active_doctors)} doctores activos")
        for doctor in active_doctors:
            print(f"  • ID: {doctor[0]}, Nombre: {doctor[1]}, Telegram ID: {doctor[2]}, Activo: {doctor[3]}")
        
        inactive_doctors = await admin_service.get_inactive_doctors()
        print(f"\nTotal: {len(inactive_doctors)} doctores inactivos")
        for doctor in inactive_doctors:
            print(f"  • ID: {doctor[0]}, Nombre: {doctor[1]}, Telegram ID: {doctor[2]}, Activo: {doctor[3]}")
        
        # PRUEBA 2: Consulta directa a la base de datos
        print("\n📋 PRUEBA 2: Consulta directa a la base de datos")
        print("-" * 60)
        async with get_session() as session:
            # Todos los doctores (sin filtrar)
            stmt_all = select(Doctor)
            result_all = await session.execute(stmt_all)
            all_doctors_db = result_all.scalars().all()
            print(f"Total doctores en BD (sin filtrar): {len(all_doctors_db)}")
            for doctor in all_doctors_db:
                print(f"  • ID: {doctor.id}, Nombre: {doctor.name}, Telegram ID: {doctor.telegram_id}, Activo: {doctor.is_active}")
            
            # Solo activos
            stmt_active = select(Doctor).where(Doctor.is_active == True)
            result_active = await session.execute(stmt_active)
            active_doctors_db = result_active.scalars().all()
            print(f"\nTotal doctores activos en BD: {len(active_doctors_db)}")
            for doctor in active_doctors_db:
                print(f"  • ID: {doctor.id}, Nombre: {doctor.name}, Telegram ID: {doctor.telegram_id}")
            
            # Sin SuperAdmin (id != 1)
            stmt_no_superadmin = select(Doctor).where(Doctor.id != 1)
            result_no_superadmin = await session.execute(stmt_no_superadmin)
            doctors_no_superadmin = result_no_superadmin.scalars().all()
            print(f"\nTotal doctores (sin SuperAdmin id=1): {len(doctors_no_superadmin)}")
            for doctor in doctors_no_superadmin:
                print(f"  • ID: {doctor.id}, Nombre: {doctor.name}, Telegram ID: {doctor.telegram_id}, Activo: {doctor.is_active}")
            
            # Activos sin SuperAdmin
            stmt_active_no_superadmin = select(Doctor).where(
                Doctor.is_active == True,
                Doctor.id != 1
            )
            result_active_no_superadmin = await session.execute(stmt_active_no_superadmin)
            active_no_superadmin = result_active_no_superadmin.scalars().all()
            print(f"\nTotal doctores activos (sin SuperAdmin): {len(active_no_superadmin)}")
            for doctor in active_no_superadmin:
                print(f"  • ID: {doctor.id}, Nombre: {doctor.name}, Telegram ID: {doctor.telegram_id}")
        
        # PRUEBA 3: Simular el código de list_doctors_for_modules
        print("\n📋 PRUEBA 3: Simulando list_doctors_for_modules()")
        print("-" * 60)
        all_doctors_list = [d for d in active_doctors if d[0] != 1] + [d for d in inactive_doctors if d[0] != 1]
        print(f"Total doctores (sin SuperAdmin) usando admin_service: {len(all_doctors_list)}")
        for doctor in all_doctors_list:
            print(f"  • ID: {doctor[0]}, Nombre: {doctor[1]}, Activo: {doctor[3]}")
        
        # PRUEBA 4: Verificar módulos
        print("\n📋 PRUEBA 4: Verificando módulos por doctor")
        print("-" * 60)
        for doctor in all_doctors_list[:5]:  # Solo los primeros 5
            doctor_id = doctor[0]
            doctor_name = doctor[1]
            active_modules = await extra_modules_db.get_active_modules_for_doctor(doctor_id)
            print(f"👨‍⚕️ {doctor_name} (ID: {doctor_id}): {len(active_modules)} módulos")
            if active_modules:
                print(f"   Módulos: {', '.join(active_modules)}")
        
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
    asyncio.run(test_get_doctors_production())

