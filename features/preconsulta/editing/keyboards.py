# features/preconsulta/editing/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_summary_keyboard(fields: list, section_prefix: str, next_step_callback: str) -> InlineKeyboardMarkup:
    """
    Crea un teclado de resumen genérico con botones de edición y un botón para continuar.

    :param fields: Lista de tuplas, ej: [('full_name', 'Nombre', 'ask_full_name'), ...]
    :param section_prefix: Un prefijo corto para identificar la sección, ej: 'pi'
    :param next_step_callback: El callback_data para el botón 'Todo Correcto'.
    """
    keyboard = []

    for field in fields:
        # field puede ser (key, label) o (key, label, question_key)
        if len(field) == 3:
            field_key, field_label, question_key = field
        else:
            field_key, field_label = field
            question_key = f"ask_{field_key}"

        callback_data = f"edit_{section_prefix}_{field_key}:{question_key}"
        keyboard.append([InlineKeyboardButton(f"✏️ {field_label}", callback_data=callback_data)])

    # Botón para confirmar y continuar
    keyboard.append([InlineKeyboardButton("✅ Todo Correcto, Continuar", callback_data=next_step_callback)])
    return InlineKeyboardMarkup(keyboard)

def get_med_history_summary_keyboard(editable_fields: list) -> InlineKeyboardMarkup:
    """
    Crea un teclado de resumen para la sección de Antecedentes.
    El callback_data ahora incluye la clave del texto de la pregunta.
    """
    keyboard = []

    if editable_fields:
        # editable_fields ahora será una lista de tuplas: (clave_campo, etiqueta_boton, clave_pregunta)
        for key, label, question_key in editable_fields:
            # Formato: edit_{prefix}_{clave_campo}:{clave_pregunta}
            callback_data = f"edit_mh_{key}:{question_key}"
            keyboard.append([InlineKeyboardButton(f"✏️ Corregir {label}", callback_data=callback_data)])

    keyboard.append([InlineKeyboardButton("✅ Todo Correcto, Continuar", callback_data="mh_summary_done")])

    return InlineKeyboardMarkup(keyboard)