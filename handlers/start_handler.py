"""
Handler para el comando /start y selección de médicos
"""
from telegram import Update
from telegram.ext import ContextTypes

from utils.role_manager import RoleManager
from config import DB_PATH
from features.patient_menu.patient_handler import patient_main_menu
from features.main_menu.user_handler import admin_main_menu
from features.marketing.handler import send_marketing_menu
from handlers.inactive_doctor_handler import show_inactive_doctor_message
from database.session import get_session
from database.repositories.appointment_repository import AppointmentRepository
from features.preconsulta.patient_flow.generic_flow_engine import start_preconsultation_flow

role_manager = RoleManager(DB_PATH)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja el comando /start - Detecta rol y parámetros de médico
    """
    user_id = update.effective_user.id
    args = context.args  # Parámetros después de /start
    
    # Procesar parámetros de médico (ej: /start medico_123)
    if args and args[0].startswith('medico_'):
        try:
            doctor_id = int(args[0].split('_')[1])
            # Asignar paciente al médico (solo si el médico está activo)
            doctor = await role_manager.get_doctor_by_id(doctor_id)
            if doctor and doctor[3]:
                await role_manager.assign_patient_to_doctor(user_id, doctor_id)
                await patient_main_menu(update, context, doctor_id)
            else:
                await update.message.reply_text(
                    "❌ **Médico no disponible**\n\n"
                    "El médico al que intentas acceder no está disponible.\n"
                    "Por favor, contacta directamente con tu médico.",
                    parse_mode="Markdown"
                )
            return
        except (IndexError, ValueError):
            # Si hay error en el parámetro, continuar con flujo normal
            pass

    # Otros parámetros (pueden ser añadidos aquí si es necesario)
    
    user_role = await role_manager.get_user_role(user_id)
    
    if user_role == 'superadmin':
        await send_marketing_menu(update, context, is_superadmin=True)
    elif user_role == 'doctor':
        # Mostrar directamente el menú de inquilino (doctor) en lugar del marketing
        await admin_main_menu(update, context)
        return
    if user_role == 'inactive_doctor':
        await show_inactive_doctor_message(update, context)
        return
    if user_role == 'patient':
        doctor = await role_manager.get_assigned_doctor(user_id)
        if doctor:
            # Solo mostrar el menú del paciente, NO el marketing
            await patient_main_menu(update, context, doctor[0])
        else:
            # Si no tiene doctor asignado, mostrar marketing
            await send_marketing_menu(update, context)
        return

    # Para cualquier otro rol (new_user, etc.), mostrar marketing
    if user_role not in {'superadmin', 'doctor', 'patient', 'inactive_doctor'}:
        await send_marketing_menu(update, context)

