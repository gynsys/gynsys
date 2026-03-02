import asyncio
import logging
import pytz
from datetime import datetime, timedelta

from database.session import get_session
from database.repositories.user_repository import DoctorRepository
from database.repositories.appointment_repository import AppointmentRepository, SlotRepository
from utils.reminder_service import send_daily_reminders
from database.models.appointment import Appointment
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)

# Simulamos la clase Bot para capturar mensajes en lugar de enviarlos a Telegram
class MockBot:
    async def send_message(self, chat_id, text, parse_mode=None):
        safe_text = text.encode('cp1252', 'replace').decode('cp1252')
        print(f"\n>>>> SIMULANDO MENSAJE A TELEGRAM (Chat ID: {chat_id}) <<<<")
        print(safe_text)
        print(">" * 60 + "\n")

class MockContext:
    def __init__(self):
        self.bot = MockBot()

async def setup_test_data():
    """Inserta 3 citas de prueba para hoy y 1 para mañana usando el primer doctor activo que encuentre."""
    tz = pytz.timezone('America/Caracas')
    now = datetime.now(tz)
    today_base = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    async with get_session() as session:
        doctor_repo = DoctorRepository(session)
        slot_repo = SlotRepository(session)
        appt_repo = AppointmentRepository(session)
        
        # Obtener el primer doctor
        doctors = await doctor_repo.get_all_doctors()
        if not doctors:
            print("No hay doctores activos para realizar la prueba.")
            return None, []
            
        doctor = doctors[0]
        
        # Crear 3 slots para hoy
        ts_10am = int(today_base.replace(hour=10).timestamp())
        ts_2pm = int(today_base.replace(hour=14).timestamp())
        ts_4pm = int(today_base.replace(hour=16).timestamp())
        
        # Crear 1 slot para mañana
        ts_tomorrow = int((today_base + timedelta(days=1)).replace(hour=10).timestamp())
        
        # Insertar Slots
        slot1 = await slot_repo.add_slot(doctor.id, ts_10am, 30, note="TEST")
        slot2 = await slot_repo.add_slot(doctor.id, ts_2pm, 30, note="TEST")
        slot3 = await slot_repo.add_slot(doctor.id, ts_4pm, 30, note="TEST")
        slot4 = await slot_repo.add_slot(doctor.id, ts_tomorrow, 30, note="TEST")
        
        # Reservar los appointments (El repo verifica que esté disponible, crea Appointment)
        await appt_repo.book_slot(doctor.id, slot1.id, 9991, "Paciente Test 10AM")
        await appt_repo.book_slot(doctor.id, slot2.id, 9992, "Paciente Test 2PM")
        await appt_repo.book_slot(doctor.id, slot3.id, 9993, "Paciente Test 4PM")
        await appt_repo.book_slot(doctor.id, slot4.id, 9994, "Paciente Test Mañana")

        return doctor, [slot1, slot2, slot3, slot4]

async def cleanup_test_data(doctor, slots):
    """Elimina las citas que creamos para la prueba."""
    if not doctor: return
    async with get_session() as session:
        appt_repo = AppointmentRepository(session)
        
        for slot in slots:
            result = await session.execute(select(Appointment).where(Appointment.slot_id == slot.id))
            appt = result.scalar_one_or_none()
            if appt:
                # delete_appointment elimina la cita y el cupo (slot) automáticamente.
                await appt_repo.delete_appointment(appt.id, doctor.id)

async def run_tests():
    print("Preparando base de datos de prueba...")
    doctor, slots = await setup_test_data()
    if not doctor:
        return
        
    try:
        import utils.reminder_service
        
        tz = pytz.timezone('America/Caracas')
        base_now = datetime.now(tz)
        
        # ---------------------------------------------------------
        # Prueba 1: Simulamos que son las 7:00 AM usando un parche (Monkeypatch)
        # ---------------------------------------------------------
        print("\n" + "="*50)
        print("=== TEST 1: SIMULANDO LAS 7:00 AM ===")
        print("="*50)
        context_7am = MockContext()
        mock_time_7am = base_now.replace(hour=7, minute=0, second=0)
        
        class MockDatetime7AM(datetime):
            @classmethod
            def now(cls, tz=None):
                return mock_time_7am
                
        utils.reminder_service.datetime = MockDatetime7AM
        await send_daily_reminders(context_7am)
        
        # ---------------------------------------------------------
        # Prueba 2: Simulamos que es la 1:00 PM
        # (La cita de las 10:00 AM ya debería aparecer excluida)
        # ---------------------------------------------------------
        print("\n" + "="*50)
        print("=== TEST 2: SIMULANDO LA 1:00 PM ===")
        print("="*50)
        context_1pm = MockContext()
        mock_time_1pm = base_now.replace(hour=13, minute=0, second=0)
        
        class MockDatetime1PM(datetime):
            @classmethod
            def now(cls, tz=None):
                return mock_time_1pm
                
        utils.reminder_service.datetime = MockDatetime1PM
        await send_daily_reminders(context_1pm)
        
    finally:
        utils.reminder_service.datetime = datetime # Restaurar el módulo original
        print("\nLimpiando datos de prueba de la base de datos...")
        await cleanup_test_data(doctor, slots)
        print("Limpieza completada.")

if __name__ == "__main__":
    asyncio.run(run_tests())
