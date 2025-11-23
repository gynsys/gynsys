# features/patient_archive/keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def build_patient_search_results_keyboard(results: list) -> InlineKeyboardMarkup:
    """Construye el teclado con los resultados de la búsqueda de pacientes."""
    keyboard = []
    for patient in results:
        button_text = f"👤 {patient['full_name']} (Últ. visita: {patient['last_visit']})"
        callback_data = f"view_patient_history_{patient['user_id']}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    keyboard.append([InlineKeyboardButton("🔙 ", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)


def build_patient_history_keyboard(history_list: list, user_id: int) -> InlineKeyboardMarkup:
    """
    Construye el teclado con la lista de informes completados de un paciente,
    con botones de navegación corregidos.
    """
    keyboard = []
    for history in history_list:
        visit_date = history['visit_date']
        consult_type = history.get('consultation_type', 'Consulta')

        # --- VOLVEMOS AL CALLBACK_DATA ORIGINAL Y FUNCIONAL ---
        # El 'source' es 'patientarchive', que el handler ya sabe cómo manejar.
        callback_data = f"view_history_{history['id']}_patientarchive_{user_id}"

        button_text = f"🗓️ {visit_date} - {consult_type}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    # --- INICIO DE LA MODIFICACIÓN SIMPLE Y SEGURA ---
    # Añadimos una fila de navegación con ambos botones.
    keyboard.append([
        InlineKeyboardButton("🔙 ", callback_data="patient_archive_hub")

    ])
    # --- FIN DE LA MODIFICACIÓN ---

    return InlineKeyboardMarkup(keyboard)

def get_editing_hub_keyboard(history_id: int, user_id: int = None) -> InlineKeyboardMarkup:
    """Crea el teclado para el hub de edición."""
    keyboard = [
        [InlineKeyboardButton("✍️ Examen Físico", callback_data=f"edit_field:{history_id}:admin_physical_exam")],
        [InlineKeyboardButton("🔬 Ultrasonido", callback_data=f"edit_field:{history_id}:admin_ultrasound")],
        [InlineKeyboardButton("🩺 Diagnóstico", callback_data=f"edit_field:{history_id}:admin_diagnosis")],
        [InlineKeyboardButton("📝 Plan", callback_data=f"edit_field:{history_id}:admin_plan")],
        [InlineKeyboardButton("💬 Observaciones", callback_data=f"edit_field:{history_id}:admin_observations")],
        # CAMBIO: Usar finish_editing en lugar de view_patient_history
        [InlineKeyboardButton("✅ Finalizar Edición", callback_data="patient_archive_hub")]# CAMBIO: Usar finish_editing en lugar de view_patient_history
    ]
    return InlineKeyboardMarkup(keyboard)