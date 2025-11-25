# features/preconsultas_admin/keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_editing_hub_keyboard(history_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        # CAMBIAR: usar : en lugar de _
        [InlineKeyboardButton("✍️ Examen Físico", callback_data=f"edit_field:{history_id}:admin_physical_exam")],
        [InlineKeyboardButton("🔬 Ultrasonido", callback_data=f"edit_field:{history_id}:admin_ultrasound")],
        [InlineKeyboardButton("🩺 Diagnóstico", callback_data=f"edit_field:{history_id}:admin_diagnosis")],
        [InlineKeyboardButton("📝 Plan", callback_data=f"edit_field:{history_id}:admin_plan")],
        [InlineKeyboardButton("💬 Observaciones", callback_data=f"edit_field:{history_id}:admin_observations")],
        [InlineKeyboardButton("✅ Finalizar Edición", callback_data=f"finish_editing_{history_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_pdf_actions_keyboard(history_id: int, back_callback: str, back_text: str) -> InlineKeyboardMarkup:
    """
    Crea el teclado de acciones después de generar un PDF.
    """
    keyboard = [
        [
            InlineKeyboardButton("✉️ Enviar al Paciente", callback_data=f"send_to_patient_{history_id}"),
            InlineKeyboardButton("📥 Descargar PDF", callback_data=f"download_pdf_{history_id}")
        ],
        [
            InlineKeyboardButton(back_text, callback_data=back_callback)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_add_another_keyboard(item_type: str) -> InlineKeyboardMarkup:
    """
    Crea un teclado con opciones para añadir otro ítem o continuar.
    item_type puede ser 'diagnosis' o 'plan'.
    """
    keyboard = [
        [
            InlineKeyboardButton(f"➕ Añadir otro {item_type}", callback_data=f"add_another_{item_type}"),
            InlineKeyboardButton("➡️ Continuar", callback_data=f"finish_{item_type}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def build_histories_list_keyboard(histories: list, current_page: int) -> InlineKeyboardMarkup:
    """
    Construye el teclado para la lista paginada de historias médicas.
    """
    keyboard = []

    # Crea un botón para cada historia en la lista
    for history in histories:
        callback_data = f"view_history_{history['id']}_pendinglist_{current_page}"
        # Manejar created_at que puede ser datetime o string
        created_at = history.get('created_at', '')
        if hasattr(created_at, 'strftime'):
            # Es un objeto datetime
            date_str = created_at.strftime('%Y-%m-%d')
        elif isinstance(created_at, str):
            # Es un string
            date_str = created_at.split(' ')[0] if ' ' in created_at else created_at
        else:
            date_str = '-'
        keyboard.append([InlineKeyboardButton(f"👤 {history['full_name']} ({date_str})", callback_data=callback_data)])


    # Lógica de paginación
    navigation_row = []
    if current_page > 0:
        navigation_row.append(
            InlineKeyboardButton("⬅️ Anterior", callback_data=f"list_histories_{current_page - 1}")
        )

    # Suponemos que si recibimos 10 resultados, puede haber más.
    # Es una forma simple de saber si mostrar el botón "Siguiente".
    if len(histories) == 10:
        navigation_row.append(
            InlineKeyboardButton("Siguiente ➡️", callback_data=f"list_histories_{current_page + 1}")
        )

    if navigation_row:
        keyboard.append(navigation_row)

    # Botón para volver al panel de administración
    keyboard.append([InlineKeyboardButton("🔙 ", callback_data="patient_management_hub")])

    return InlineKeyboardMarkup(keyboard)

def get_history_details_keyboard(history_id: int, status: str, back_callback: str, back_text: str) -> InlineKeyboardMarkup:
    """
    Construye el teclado para la vista de detalles, con navegación mejorada.
    """
    keyboard = []

    if status == 'pending':
        keyboard.append([
            InlineKeyboardButton("📝 Completar Informe", callback_data=f"start_consultation_{history_id}"),
            InlineKeyboardButton("🗑️ Eliminar", callback_data=f"confirm_delete_history_{history_id}")
        ])
    elif status == 'completed':
        keyboard.append([
            InlineKeyboardButton("🖨️ Historia Médica", callback_data=f"generate_pdf_{history_id}"),
            InlineKeyboardButton("📋 Informe Médico", callback_data=f"generate_summary_pdf_{history_id}")
        ])
        keyboard.append(
            [InlineKeyboardButton("✏️ Modificar Informe", callback_data=f"start_editing_{history_id}")]
        )

    # --- INICIO DE LA MODIFICACIÓN CLAVE ---
    # Creamos una fila de navegación final con ambos botones: Volver y Menú Principal.
    navigation_row = [
        InlineKeyboardButton(back_text, callback_data=back_callback),
        InlineKeyboardButton("🏠 ", callback_data="main_menu")
    ]
    keyboard.append(navigation_row)
    # --- FIN DE LA MODIFICACIÓN CLAVE ---

    return InlineKeyboardMarkup(keyboard)



