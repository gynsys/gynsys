"""
Script de prueba para verificar que MedicalRepository funciona correctamente.
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.engine import init_engine, close_engine
from database.session import get_session
from database.repositories.medical_repository import MedicalRepository, SENSITIVE_FIELDS
from database.repositories.user_repository import DoctorRepository


async def test_medical_repository():
    """Prueba las operaciones del MedicalRepository"""
    print("🔧 Inicializando engine...")
    await init_engine()
    
    try:
        print("✅ Engine inicializado correctamente\n")
        
        async with get_session() as session:
            repo = MedicalRepository(session)
            doctor_repo = DoctorRepository(session)
            
            # Obtener un doctor de prueba
            doctors = await doctor_repo.get_all_doctors()
            if not doctors:
                print("⚠️ No hay doctores para probar historiales médicos")
                return
            
            test_doctor = doctors[0]
            test_doctor_id = test_doctor.id
            test_user_id = 999999999
            
            print(f"📋 Probando con doctor ID: {test_doctor_id} ({test_doctor.name})\n")
            
            # 1. Crear una historia médica de prueba
            print("1️⃣ Probando save_history (con encriptación)...")
            test_data = {
                'doctor_id': test_doctor_id,
                'user_id': test_user_id,
                'full_name': 'Paciente de Prueba',
                'age': '30',
                'phone': '1234567890',
                'reason_for_visit': 'Consulta de prueba',
                'status': 'pending'
            }
            history_id = await repo.save_history(test_data)
            if history_id:
                print(f"   ✅ Historia creada: ID={history_id}\n")
            else:
                print("   ❌ Error al crear historia\n")
                return
            
            # 2. Obtener detalles de la historia
            print(f"2️⃣ Probando get_history_details ({history_id})...")
            details = await repo.get_history_details(history_id, test_doctor_id)
            if details:
                print(f"   ✅ Historia encontrada")
                print(f"      - Nombre (descifrado): {details.get('full_name')}")
                print(f"      - Teléfono (descifrado): {details.get('phone')}\n")
            else:
                print("   ❌ Historia no encontrada\n")
            
            # 3. Obtener historiales pendientes
            print("3️⃣ Probando get_all_histories...")
            histories = await repo.get_all_histories(test_doctor_id, limit=5)
            print(f"   ✅ Historiales pendientes: {len(histories)}\n")
            
            # 4. Verificar si usuario es recurrente
            print(f"4️⃣ Probando check_if_user_is_recurrent ({test_user_id})...")
            recurrent = await repo.check_if_user_is_recurrent(test_user_id, test_doctor_id)
            if recurrent:
                print(f"   ✅ Usuario recurrente: {recurrent.get('full_name')}\n")
            else:
                print("   ℹ️ Usuario nuevo\n")
            
            # 5. Actualizar campo específico
            print(f"5️⃣ Probando update_history_field ({history_id})...")
            updated = await repo.update_history_field(history_id, 'age', '31')
            print(f"   ✅ Campo actualizado: {updated}\n")
            
            # 6. Generar número de historia
            print("6️⃣ Probando get_next_history_number...")
            history_number = await repo.get_next_history_number(test_doctor_id, "Ginecológica")
            print(f"   ✅ Número de historia generado: {history_number}\n")
            
            # 7. Guardar número de historia
            print(f"7️⃣ Probando save_history_number ({history_id})...")
            saved = await repo.save_history_number(history_id, history_number)
            print(f"   ✅ Número guardado: {saved}\n")
            
            # 8. Completar historia
            print(f"8️⃣ Probando complete_history ({history_id})...")
            admin_data = {
                'admin_diagnosis': 'Diagnóstico de prueba',
                'admin_plan': 'Plan de prueba'
            }
            completed = await repo.complete_history(history_id, test_doctor_id, admin_data)
            print(f"   ✅ Historia completada: {completed}\n")
            
            # 9. Obtener historiales completados
            print("9️⃣ Probando get_latest_completed_histories...")
            completed_histories = await repo.get_latest_completed_histories(test_doctor_id, limit=5)
            print(f"   ✅ Historiales completados: {len(completed_histories)}\n")
            
            # 10. Buscar por nombre
            print("🔟 Probando search_completed_histories_by_name...")
            search_results = await repo.search_completed_histories_by_name(test_doctor_id, "Prueba")
            print(f"   ✅ Resultados de búsqueda: {len(search_results)}\n")
            
            # 11. Obtener lista de historiales del paciente
            print(f"1️⃣1️⃣ Probando get_patient_history_list ({test_user_id})...")
            patient_histories = await repo.get_patient_history_list(test_doctor_id, test_user_id)
            print(f"   ✅ Historiales del paciente: {len(patient_histories)}\n")
            
            # 12. Eliminar historia de prueba
            print(f"1️⃣2️⃣ Probando delete_history ({history_id})...")
            deleted = await repo.delete_history(history_id)
            print(f"   ✅ Historia eliminada: {deleted}\n")
            
            await session.commit()
        
        print("✅ Todas las pruebas del MedicalRepository pasaron correctamente!")
        
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
    print("🧪 PRUEBA DE MEDICAL REPOSITORY")
    print("=" * 60 + "\n")
    asyncio.run(test_medical_repository())
    print("\n" + "=" * 60)

