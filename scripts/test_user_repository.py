"""
Script de prueba para verificar que UserRepository funciona correctamente.
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.engine import init_engine, close_engine
from database.session import get_session
from database.repositories.user_repository import DoctorRepository, PatientDoctorRepository
from config import SUPER_ADMIN_ID


async def test_doctor_repository():
    """Prueba las operaciones del DoctorRepository"""
    print("🔧 Inicializando engine...")
    await init_engine()
    
    try:
        print("✅ Engine inicializado correctamente\n")
        
        async with get_session() as session:
            repo = DoctorRepository(session)
            
            # 1. Obtener todos los doctores
            print("1️⃣ Probando get_all_doctors...")
            doctors = await repo.get_all_doctors()
            print(f"   ✅ Doctores encontrados: {len(doctors)}")
            if doctors:
                print(f"      Primer doctor: {doctors[0].name} (ID: {doctors[0].id})\n")
            
            # 2. Obtener doctor por telegram_id
            if doctors:
                test_telegram_id = doctors[0].telegram_id
                print(f"2️⃣ Probando get_doctor_by_telegram_id ({test_telegram_id})...")
                doctor = await repo.get_doctor_by_telegram_id(test_telegram_id)
                if doctor:
                    print(f"   ✅ Doctor encontrado: {doctor.name}\n")
                else:
                    print("   ⚠️ Doctor no encontrado\n")
            
            # 3. Obtener doctor por ID
            if doctors:
                test_id = doctors[0].id
                print(f"3️⃣ Probando get_doctor_by_id ({test_id})...")
                doctor = await repo.get_doctor_by_id(test_id)
                if doctor:
                    print(f"   ✅ Doctor encontrado: {doctor.name}\n")
            
            # 4. Obtener doctores inactivos
            print("4️⃣ Probando get_inactive_doctors...")
            inactive = await repo.get_inactive_doctors()
            print(f"   ✅ Doctores inactivos: {len(inactive)}\n")
            
            # 5. Probar activar/desactivar (solo si hay doctores)
            if doctors:
                test_id = doctors[0].id
                print(f"5️⃣ Probando activate_doctor y delete_doctor ({test_id})...")
                
                # Desactivar
                deactivated = await repo.delete_doctor(test_id)
                print(f"   ✅ Doctor desactivado: {deactivated}")
                
                # Verificar que está inactivo
                doctor = await repo.get_doctor_by_id(test_id)
                if doctor and not doctor.is_active:
                    print(f"   ✅ Doctor está inactivo\n")
                
                # Reactivar
                activated = await repo.activate_doctor(test_id)
                print(f"   ✅ Doctor reactivado: {activated}")
                
                # Verificar que está activo
                doctor = await repo.get_doctor_by_id(test_id)
                if doctor and doctor.is_active:
                    print(f"   ✅ Doctor está activo\n")
            
            # 6. Probar get_any_doctor_by_telegram_id
            if doctors:
                test_telegram_id = doctors[0].telegram_id
                print(f"6️⃣ Probando get_any_doctor_by_telegram_id ({test_telegram_id})...")
                doctor = await repo.get_any_doctor_by_telegram_id(test_telegram_id)
                if doctor:
                    print(f"   ✅ Doctor encontrado (activo o inactivo): {doctor.name}\n")
            
            # 7. Probar cleanup_doctor_patient_associations
            print("7️⃣ Probando cleanup_doctor_patient_associations...")
            cleaned = await repo.cleanup_doctor_patient_associations()
            print(f"   ✅ Asociaciones limpiadas: {cleaned}\n")
            
            await session.commit()
        
        print("✅ Todas las pruebas del DoctorRepository pasaron correctamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()


async def test_patient_doctor_repository():
    """Prueba las operaciones del PatientDoctorRepository"""
    print("\n" + "=" * 60)
    print("🧪 PRUEBA DE PATIENT DOCTOR REPOSITORY")
    print("=" * 60 + "\n")
    
    try:
        async with get_session() as session:
            patient_repo = PatientDoctorRepository(session)
            doctor_repo = DoctorRepository(session)
            
            # Obtener un doctor de prueba
            doctors = await doctor_repo.get_all_doctors()
            if not doctors:
                print("⚠️ No hay doctores para probar asociaciones")
                return
            
            test_doctor = doctors[0]
            test_patient_id = 999999999  # ID de prueba
            
            # 1. Asignar paciente a doctor
            print(f"1️⃣ Probando assign_patient_to_doctor...")
            print(f"   Paciente: {test_patient_id}, Doctor: {test_doctor.name} (ID: {test_doctor.id})")
            association = await patient_repo.assign_patient_to_doctor(
                test_patient_id, 
                test_doctor.id
            )
            print(f"   ✅ Asociación creada: {association}\n")
            
            # 2. Obtener doctor para paciente
            print(f"2️⃣ Probando get_doctor_for_patient ({test_patient_id})...")
            doctor = await patient_repo.get_doctor_for_patient(test_patient_id)
            if doctor:
                print(f"   ✅ Doctor encontrado: {doctor.name}\n")
            
            # 3. Obtener pacientes de un doctor
            print(f"3️⃣ Probando get_patients_for_doctor ({test_doctor.id})...")
            patients = await patient_repo.get_patients_for_doctor(test_doctor.id)
            print(f"   ✅ Pacientes encontrados: {len(patients)}\n")
            
            # 4. Eliminar asociación
            print(f"4️⃣ Probando remove_association...")
            removed = await patient_repo.remove_association(
                test_patient_id,
                test_doctor.id
            )
            print(f"   ✅ Asociación eliminada: {removed}\n")
            
            await session.commit()
        
        print("✅ Todas las pruebas del PatientDoctorRepository pasaron correctamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Ejecuta todas las pruebas"""
    print("=" * 60)
    print("🧪 PRUEBA DE USER REPOSITORY")
    print("=" * 60 + "\n")
    
    await test_doctor_repository()
    await test_patient_doctor_repository()
    
    print("\n" + "=" * 60)
    print("🔒 Cerrando engine...")
    await close_engine()
    print("✅ Engine cerrado correctamente")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

