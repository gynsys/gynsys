import logging
from datetime import datetime
import pytz
from telegram.ext import ContextTypes
from database.session import get_session
from database.repositories.user_repository import DoctorRepository
from database.repositories.appointment_repository import AppointmentRepository

logger = logging.getLogger(__name__)

async def send_daily_reminders(context: ContextTypes.DEFAULT_TYPE):
    """
    Envía recordatorios diarios de citas a los médicos.
    
    Esta función se ejecuta dos veces al día:
    - 7:00 AM: Envía todas las citas del día.
    - 1:00 PM: Envía solo las citas restantes para la tarde.
    
    Solo incluye citas cuya hora aún no ha pasado en el momento de la ejecución.
    """
    logger.info("Iniciando envío de recordatorios diarios de citas a los doctores...")
    
    # Usar hora local de Venezuela
    tz = pytz.timezone('America/Caracas')
    now = datetime.now(tz)
    
    # Inicio y fin del día actual (timestamp unix)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    start_ts = int(start_of_day.timestamp())
    end_ts = int(end_of_day.timestamp())
    
    # Filtrar citas que ya pasaron
    current_ts = int(now.timestamp())
    
    # Identificar si es el recordatorio de la mañana o de la tarde
    is_morning = now.hour < 12
    greeting_period = "del día" if is_morning else "de la tarde"
    greeting_word = "Buenos días" if is_morning else "Buenas tardes"

    sent_count = 0
    
    try:
        async with get_session() as session:
            doctor_repo = DoctorRepository(session)
            appointment_repo = AppointmentRepository(session)
            
            doctors = await doctor_repo.get_all_doctors()
            
            for doctor in doctors:
                try:
                    # Obtener las citas programadas para el doctor
                    appointments = await appointment_repo.get_appointments_for_doctor(
                        doctor.id, 
                        statuses=["pending", "confirmed"]
                    )
                    
                    # Filtrar las citas que corresponden al día de hoy Y que no hayan pasado
                    todays_appointments = []
                    for appt in appointments:
                        appt_ts = appt.get('start_ts')
                        if appt_ts and start_ts <= appt_ts <= end_ts:
                            if appt_ts >= current_ts:
                                todays_appointments.append(appt)

                    if not todays_appointments:
                        # Si no hay citas para lo que resta del día, no enviar mensaje
                        continue
                        
                    # Formatear el mensaje
                    message_lines = [
                        f"📅 *Recordatorio de Citas*",
                        f"¡{greeting_word}, Dr(a). {doctor.name}! Tienes {len(todays_appointments)} cita(s) programada(s) para el resto {greeting_period}:\n"
                    ]
                    
                    for appt in todays_appointments:
                        # Convertir timestamp a string de hora legible en zona local
                        appt_dt = datetime.fromtimestamp(appt['start_ts'], tz=tz)
                        time_str = appt_dt.strftime("%I:%M %p")
                        
                        patient_name = appt.get('patient_name', 'Paciente Anónimo')
                        message_lines.append(f"▫️ {time_str} - {patient_name}")
                        
                    message_text = "\n".join(message_lines)
                    
                    # Enviar mensaje al doctor
                    await context.bot.send_message(
                        chat_id=doctor.telegram_id,
                        text=message_text,
                        parse_mode="Markdown"
                    )
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error enviando recordatorio al doctor ID {doctor.id} ({doctor.name}): {e}")
                    # Continuar con el siguiente doctor
                    continue
                    
        logger.info(f"✅ Recordatorios diarios enviados exitosamente a {sent_count} doctores.")
    except Exception as e:
        logger.error(f"Error crítico en la rutina de recordatorios diarios: {e}", exc_info=True)
