"""
Script de prueba para verificar que AppointmentRepository funciona correctamente.
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.engine import init_engine, close_engine
from database.session import get_session
from database.repositories.appointment_repository import SlotRepository, AppointmentRepository
from database.repositories.user_repository import DoctorRepository


async def test_slot_repository():
    """Prueba las operaciones del SlotRepository"""
    print("🔧 Inicializando engine...")
    await init_engine()
    
    try:
        print("✅ Engine inicializado correctamente\n")
        
        async with get_session() as session:
            slot_repo = SlotRepository(session)
            doctor_repo = DoctorRepository(session)
            
            # Obtener un doctor de prueba
            doctors = await doctor_repo.get_all_doctors()
            if not doctors:
                print("⚠️ No hay doctores para probar slots")
                return
            
            test_doctor = doctors[0]
            test_doctor_id = test_doctor.id
            print(f"📋 Probando con doctor ID: {test_doctor_id} ({test_doctor.name})\n")
            
            # 1. Crear un slot
            print("1️⃣ Probando add_slot...")
            future_ts = int((datetime.utcnow() + timedelta(days=7)).timestamp())
            slot = await slot_repo.add_slot(
                doctor_id=test_doctor_id,
                start_ts=future_ts,
                duration_min=30,
                note="Slot de prueba"
            )
            print(f"   ✅ Slot creado: ID={slot.id}, start_ts={slot.start_ts}\n")
            
            # 2. Listar slots activos
            print("2️⃣ Probando list_active_slots...")
            now_ts = int(datetime.utcnow().timestamp())
            slots = await slot_repo.list_active_slots(test_doctor_id, now_ts)
            print(f"   ✅ Slots disponibles: {len(slots)}\n")
            
            # 3. Obtener slot por ID
            print(f"3️⃣ Probando get_slot_by_id ({slot.id})...")
            found_slot = await slot_repo.get_slot_by_id(slot.id, test_doctor_id)
            if found_slot:
                print(f"   ✅ Slot encontrado: {found_slot.note}\n")
            
            # 4. Probar eliminar slot (solo si no tiene appointments)
            print(f"4️⃣ Probando delete_slot ({slot.id})...")
            deleted = await slot_repo.delete_slot(test_doctor_id, slot.id)
            print(f"   ✅ Slot eliminado: {deleted}\n")
            
            await session.commit()
        
        print("✅ Todas las pruebas del SlotRepository pasaron correctamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()


async def test_appointment_repository():
    """Prueba las operaciones del AppointmentRepository"""
    print("\n" + "=" * 60)
    print("🧪 PRUEBA DE APPOINTMENT REPOSITORY")
    print("=" * 60 + "\n")
    
    try:
        async with get_session() as session:
            appointment_repo = AppointmentRepository(session)
            slot_repo = SlotRepository(session)
            doctor_repo = DoctorRepository(session)
            
            # Obtener un doctor de prueba
            doctors = await doctor_repo.get_all_doctors()
            if not doctors:
                print("⚠️ No hay doctores para probar appointments")
                return
            
            test_doctor = doctors[0]
            test_doctor_id = test_doctor.id
            test_patient_id = 999999999
            test_patient_name = "Paciente de Prueba"
            
            # 1. Crear un slot para reservar
            print("1️⃣ Creando slot para reservar...")
            future_ts = int((datetime.utcnow() + timedelta(days=7)).timestamp())
            slot = await slot_repo.add_slot(
                doctor_id=test_doctor_id,
                start_ts=future_ts,
                duration_min=30,
                note="Slot para prueba de appointment"
            )
            print(f"   ✅ Slot creado: ID={slot.id}\n")
            
            # 2. Reservar el slot
            print("2️⃣ Probando book_slot...")
            booked = await appointment_repo.book_slot(
                doctor_id=test_doctor_id,
                slot_id=slot.id,
                patient_telegram_id=test_patient_id,
                patient_name=test_patient_name,
                consultation_type="Consulta de prueba",
                reason="Prueba del sistema",
                location="Ubicación de prueba",
                status="pending"
            )
            print(f"   ✅ Slot reservado: {booked}\n")
            
            # 3. Obtener appointments del doctor
            print("3️⃣ Probando get_appointments_for_doctor...")
            appointments = await appointment_repo.get_appointments_for_doctor(test_doctor_id)
            print(f"   ✅ Appointments encontrados: {len(appointments)}")
            if appointments:
                app = appointments[0]
                print(f"      - Paciente: {app.get('patient_name')}, Estado: {app.get('status')}\n")
            
            # 4. Obtener appointment por ID
            if appointments:
                app_id = appointments[0]['id']
                print(f"4️⃣ Probando get_appointment_by_id ({app_id})...")
                appointment = await appointment_repo.get_appointment_by_id(app_id, test_doctor_id)
                if appointment:
                    print(f"   ✅ Appointment encontrado: {appointment.get('patient_name')}\n")
            
            # 5. Actualizar estado
            if appointments:
                app_id = appointments[0]['id']
                print(f"5️⃣ Probando update_appointment_status ({app_id})...")
                updated = await appointment_repo.update_appointment_status(
                    app_id, test_doctor_id, "confirmed"
                )
                print(f"   ✅ Estado actualizado: {updated}\n")
            
            # 6. Actualizar tiempo
            if appointments:
                app_id = appointments[0]['id']
                new_ts = int((datetime.utcnow() + timedelta(days=8)).timestamp())
                print(f"6️⃣ Probando update_appointment_time ({app_id})...")
                updated = await appointment_repo.update_appointment_time(
                    app_id, test_doctor_id, new_ts
                )
                print(f"   ✅ Tiempo actualizado: {updated}\n")
            
            # 7. Eliminar appointment
            if appointments:
                app_id = appointments[0]['id']
                print(f"7️⃣ Probando delete_appointment ({app_id})...")
                deleted = await appointment_repo.delete_appointment(app_id, test_doctor_id)
                print(f"   ✅ Appointment eliminado: {deleted}\n")
            
            await session.commit()
        
        print("✅ Todas las pruebas del AppointmentRepository pasaron correctamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Ejecuta todas las pruebas"""
    print("=" * 60)
    print("🧪 PRUEBA DE APPOINTMENT REPOSITORY")
    print("=" * 60 + "\n")
    
    await test_slot_repository()
    await test_appointment_repository()
    
    print("\n" + "=" * 60)
    print("🔒 Cerrando engine...")
    await close_engine()
    print("✅ Engine cerrado correctamente")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

