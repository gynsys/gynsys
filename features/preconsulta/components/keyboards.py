# features/preconsulta/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
from common import texts

def get_month_year_picker_keyboard(callback_prefix: str, year: int, allow_text: str = None):
    """
    Crea un teclado dinámico para seleccionar Mes y Año.
    """
    keyboard = []

    # Fila con el año actual y navegación
    nav_year_row = [
        InlineKeyboardButton("⏪ Año", callback_data=f"{callback_prefix}_nav_{year - 1}"),
        InlineKeyboardButton(f"🗓️ {year} 🗓️", callback_data=f"{callback_prefix}_ignore"),
        InlineKeyboardButton("Año ⏩", callback_data=f"{callback_prefix}_nav_{year + 1}")
    ]
    keyboard.append(nav_year_row)

    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    # Crear la cuadrícula de meses 4x3
    for i in range(0, 12, 4):
        row = []
        for j in range(4):
            month_index = i + j
            month_name = meses[month_index]
            # Formato de guardado: YYYY-MM (ej. 2025-11)
            callback_data = f"{callback_prefix}_select_{year}-{month_index + 1:02d}"
            row.append(InlineKeyboardButton(month_name, callback_data=callback_data))
        keyboard.append(row)

    # Añadir el botón "Nunca" si está permitido en el nodo JSON
    if allow_text:
        keyboard.append([InlineKeyboardButton(f"🚫 {allow_text}", callback_data=f"{callback_prefix}_{allow_text.lower()}")])

    return InlineKeyboardMarkup(keyboard)

def get_numeric_keypad_keyboard(callback_prefix: str, display_value: str = "___"):
    """Crea un teclado numérico con un botón que actúa como pantalla."""
    # Si por alguna razón el display_value está vacío, mostramos los guiones
    if not display_value:
        display_value = "___"

    keyboard = [
        # Fila 1: La "pantalla" donde se muestra el número. No es clicable.
        [InlineKeyboardButton(f"🔢 {display_value}", callback_data=f"{callback_prefix}_ignore")],

        # Filas 2-4: Los números
        [
            InlineKeyboardButton("1", callback_data=f"{callback_prefix}_digit_1"),
            InlineKeyboardButton("2", callback_data=f"{callback_prefix}_digit_2"),
            InlineKeyboardButton("3", callback_data=f"{callback_prefix}_digit_3"),
        ],
        [
            InlineKeyboardButton("4", callback_data=f"{callback_prefix}_digit_4"),
            InlineKeyboardButton("5", callback_data=f"{callback_prefix}_digit_5"),
            InlineKeyboardButton("6", callback_data=f"{callback_prefix}_digit_6"),
        ],
        [
            InlineKeyboardButton("7", callback_data=f"{callback_prefix}_digit_7"),
            InlineKeyboardButton("8", callback_data=f"{callback_prefix}_digit_8"),
            InlineKeyboardButton("9", callback_data=f"{callback_prefix}_digit_9"),
        ],

        # Fila 5: Acciones
        [
            InlineKeyboardButton("Borrar Todo", callback_data=f"{callback_prefix}_action_clear"),
            InlineKeyboardButton("0", callback_data=f"{callback_prefix}_digit_0"),
            InlineKeyboardButton("⌫ Borrar", callback_data=f"{callback_prefix}_action_backspace"),
        ],

        # Fila 6: Envío
        [InlineKeyboardButton("✅ Aceptar y Continuar", callback_data=f"{callback_prefix}_action_submit")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_sexarche_grid_keyboard(callback_prefix: str, start_age: int):
    """
    Crea una cuadrícula de 3x3 para la edad de sexarquia, con navegación.
    """
    keyboard = []
    current_age = start_age
    for _ in range(3):
        row = []
        for _ in range(3):
            age_str = str(current_age)
            row.append(InlineKeyboardButton(age_str, callback_data=f"{callback_prefix}_select_{age_str}"))
            current_age += 1
        keyboard.append(row)

    nav_row = [
        InlineKeyboardButton("⏪", callback_data=f"{callback_prefix}_nav_{start_age - 9}"),
        InlineKeyboardButton("No he tenido", callback_data=f"{callback_prefix}_select_Nunca"),
        InlineKeyboardButton("⏩", callback_data=f"{callback_prefix}_nav_{start_age + 9}")
    ]
    keyboard.append(nav_row)
    return InlineKeyboardMarkup(keyboard)

def get_number_grid_keyboard(callback_prefix: str, start: int, end: int, cols: int):
    """
    Crea una cuadrícula de botones numéricos desde un número 'start' hasta 'end'.
    """
    keyboard = []
    row = []
    for i in range(start, end + 1):
        row.append(InlineKeyboardButton(str(i), callback_data=f"{callback_prefix}_select_{i}"))
        if len(row) == cols:
            keyboard.append(row)
            row = []
    if row: # Añadir la última fila si no está completa
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def get_birth_complications_keyboard(callback_prefix: str, selected: set = None):
    """Crea un teclado de checklist para complicaciones del parto."""
    if selected is None: selected = set()
    complications = {
        "preeclampsia": "Preclamsia",
        "placenta_previa": "Placenta Previa",
        "hemorragia": "Hemorragias",
        "none": "Sin complicaciones"
    }
    keyboard = []
    for key, text in complications.items():
        prefix = "✅ " if key in selected else ""
        keyboard.append([InlineKeyboardButton(f"{prefix}{text}", callback_data=f"{callback_prefix}_{key}")])
    keyboard.append([InlineKeyboardButton("➡️ Siguiente", callback_data=f"{callback_prefix}_done")])
    return InlineKeyboardMarkup(keyboard)

def get_ho_table_keyboard(callback_prefix: str, selections: dict = None):
    if selections is None: selections = {}

    # Usamos claves de textos.json para las etiquetas
    categories = {
        'single_pregnancies': 'preconsulta.ho_table_label_single',
        'multiple_pregnancies': 'preconsulta.ho_table_label_multiple',
        'abortions': 'Abortos' # Podemos dejar este simple
    }

    number_options = list(range(1, 8))
    keyboard = []

    for key, label_key in categories.items():
        # Obtenemos el texto desde texts.json, o usamos la clave si no se encuentra
        label = texts.get_text(label_key, label_key.replace('_', ' ').title())

        keyboard.append([InlineKeyboardButton(f"--- {label} ---", callback_data=f"{callback_prefix}_ignore")])

        row_buttons = []
        selected_value = selections.get(key)
        for num in number_options:
            text = f"✅ {num}" if selected_value == num else str(num)
            row_buttons.append(InlineKeyboardButton(text, callback_data=f"{callback_prefix}_{key}_{num}"))
        keyboard.append(row_buttons)

    keyboard.append([InlineKeyboardButton("➡️ Guardar y Continuar", callback_data=f"{callback_prefix}_done")])
    return InlineKeyboardMarkup(keyboard)

def get_year_grid_keyboard(callback_prefix: str, end_year: int = None):
    """
    Crea un teclado de cuadrícula de 5x3 (15 años) decreciente para seleccionar un año.
    """
    if end_year is None:
        end_year = datetime.now().year

    # El año de inicio del bloque es el año final menos 14 (para un total de 15 años)
    start_year = end_year - 14

    keyboard = []
    current_year_in_grid = start_year

    # Generar la cuadrícula de 5 filas y 3 columnas
    for _ in range(5):
        row = []
        for _ in range(3):
            year_str = str(current_year_in_grid)
            row.append(
                InlineKeyboardButton(
                    year_str,
                    callback_data=f"{callback_prefix}_select_{year_str}"
                )
            )
            current_year_in_grid += 1
        keyboard.append(row)

    # Añadir la última fila de botones de navegación en bloques de 15 años
    nav_row = [
        InlineKeyboardButton("⏪ 15 Años", callback_data=f"{callback_prefix}_nav_{end_year - 15}"),
        InlineKeyboardButton("Actual ⏩", callback_data=f"{callback_prefix}_nav_{datetime.now().year}")
    ]
    keyboard.append(nav_row)

    return InlineKeyboardMarkup(keyboard)

def get_substances_keyboard(callback_prefix: str, selected: set = None):
    """Crea un teclado de checklist para tipos de sustancias."""
    if selected is None: selected = set()
    substances = {

        "cannabis": "🌿 Marihuana/cannabis", "cocaine": "❄️ Cocaína",
        "amphetamines": "💊 Anfetaminas", "opioids": "💊 Opioides",
        "benzos": "😴 Benzodiacepinas", "hallucinogens": "🍄A lucinógenos",
        "other": "💉 Otras sustancias"
    }
    keyboard = []
    for key, text in substances.items():
        prefix = "✅ " if key in selected else ""
        keyboard.append([InlineKeyboardButton(f"{prefix}{text}", callback_data=f"{callback_prefix}_{key}")])
    keyboard.append([InlineKeyboardButton("➡️ Terminar y Siguiente", callback_data=f"{callback_prefix}_done")])
    return InlineKeyboardMarkup(keyboard)

def get_leg_pain_type_keyboard(callback_prefix: str, selected: set = None):
    """Crea un teclado para el TIPO de dolor en piernas."""
    if selected is None: selected = set()
    types = {
        "punzante": "Punzante", "quemante": "Quemante",
        "corriente": "Corriente", "hormigueo": "Hormigueo"
    }
    keyboard = []
    for key, text in types.items():
        prefix = "✅ " if key in selected else ""
        # Usamos el prefijo dinámico
        keyboard.append([InlineKeyboardButton(f"{prefix}{text}", callback_data=f"{callback_prefix}_{key}")])
    keyboard.append([InlineKeyboardButton("➡️ Siguiente", callback_data=f"{callback_prefix}_done")])
    return InlineKeyboardMarkup(keyboard)

def get_leg_pain_zone_keyboard(callback_prefix: str, selected: set = None):
    """Crea un teclado para la ZONA del dolor en piernas."""
    if selected is None: selected = set()
    zones = {
        "lateral": "Lateral", "interna": "Interna",
        "posterior": "Posterior", "gluteos": "Zona de glúteos"
    }
    keyboard = []
    for key, text in zones.items():
        prefix = "✅ " if key in selected else ""
        # Usamos el prefijo dinámico
        keyboard.append([InlineKeyboardButton(f"{prefix}{text}", callback_data=f"{callback_prefix}_{key}")])
    keyboard.append([InlineKeyboardButton("➡️ Terminar y Siguiente", callback_data=f"{callback_prefix}_done")])
    return InlineKeyboardMarkup(keyboard)

def get_mac_keyboard(callback_prefix: str, selected: set = None):
    if selected is None: selected = set()

    # Usamos claves simples para el callback_data
    options = {
    "pastillas": "Pastillas", "diu": "DIU", "inyeccion": "Inyección", "implante": "Implante",
    "anillo": "Anillo Vaginal", "parche": "Parche", "condones": "Condones",
    "ritmo": "Método del Ritmo", "coitus_interruptus": "Coitus Interruptus"
    }

    keyboard = []
    options_items = list(options.items())
    for i in range(0, len(options_items), 2):
        row = []
        key1, text1 = options_items[i]
        # Usamos la clave (ej. "pastillas") en el callback
        prefix1 = "✅ " if key1 in selected else ""
        row.append(InlineKeyboardButton(f"{prefix1}{text1}", callback_data=f"{callback_prefix}_{key1}"))

        if i + 1 < len(options_items):
            key2, text2 = options_items[i+1]
            prefix2 = "✅ " if key2 in selected else ""
            row.append(InlineKeyboardButton(f"{prefix2}{text2}", callback_data=f"{callback_prefix}_{key2}"))
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("➡️ Terminar y Siguiente", callback_data=f"{callback_prefix}_done")])
    return InlineKeyboardMarkup(keyboard)


def get_sexual_pain_type_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Superficial", callback_data="pain_type_superficial")],
        [InlineKeyboardButton("Profunda", callback_data="pain_type_profunda")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_dischezia_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("👍 Sí", callback_data="dischezia_yes"),
            InlineKeyboardButton("👎 No", callback_data="dischezia_no"),
            InlineKeyboardButton("+/- Eventual", callback_data="dischezia_eventual"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_bowel_frequency_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("Diario", callback_data="bowel_freq_daily")],
        [InlineKeyboardButton("Cada 1 día", callback_data="bowel_freq_1d"), InlineKeyboardButton("Cada 2 días", callback_data="bowel_freq_2d")],
        [InlineKeyboardButton("Cada 3 días", callback_data="bowel_freq_3d"), InlineKeyboardButton("Cada 4 días", callback_data="bowel_freq_4d")],
        [InlineKeyboardButton("Cada 5 días", callback_data="bowel_freq_5d"), InlineKeyboardButton("Semanal", callback_data="bowel_freq_weekly")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_pain_scale_keyboard(callback_prefix: str) -> InlineKeyboardMarkup:
    """
    Crea un teclado interactivo para la escala de dolor (EVA), ahora con un prefijo dinámico.
    """
    keyboard = [
        [InlineKeyboardButton("0️⃣ Sin Dolor", callback_data=f"{callback_prefix}_0")],
        [
            InlineKeyboardButton("Leve", callback_data=f"{callback_prefix}_ignore"),
            InlineKeyboardButton("1️⃣", callback_data=f"{callback_prefix}_1"),
            InlineKeyboardButton("2️⃣", callback_data=f"{callback_prefix}_2"),
            InlineKeyboardButton("3️⃣", callback_data=f"{callback_prefix}_3"),
        ], # <-- CORRECCIÓN: La coma va aquí
        [
            InlineKeyboardButton("Moderado", callback_data=f"{callback_prefix}_ignore"),
            InlineKeyboardButton("4️⃣", callback_data=f"{callback_prefix}_4"),
            InlineKeyboardButton("5️⃣", callback_data=f"{callback_prefix}_5"),
            InlineKeyboardButton("6️⃣", callback_data=f"{callback_prefix}_6"),
        ],
        [
            InlineKeyboardButton("Intenso", callback_data=f"{callback_prefix}_ignore"),
            InlineKeyboardButton("7️⃣", callback_data=f"{callback_prefix}_7"),
            InlineKeyboardButton("8️⃣", callback_data=f"{callback_prefix}_8"),
            InlineKeyboardButton("9️⃣", callback_data=f"{callback_prefix}_9"),
            InlineKeyboardButton("🔟", callback_data=f"{callback_prefix}_10"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_gastro_symptoms_keyboard(callback_prefix: str, selected: set = None):
    """Crea un teclado de checklist genérico para síntomas gastrointestinales."""
    if selected is None:
        selected = set()

    symptoms = {
        "nauseas": "Nauseas",
        "vomitos": "Vómitos",
        "inflamacion": "Inflamación",
        "distension": "Distensión abdominal",
        "dolor_evacuar": "Dolor al evacuar",
        "colicos": "Cólicos",
        "flatulencias": "Flatulencias"
    }

    keyboard = []
    for key, text in symptoms.items():
        prefix = "✅ " if key in selected else ""
        keyboard.append([InlineKeyboardButton(f"{prefix}{text}", callback_data=f"{callback_prefix}_{key}")])

    keyboard.append([InlineKeyboardButton("➡️ Terminar y Siguiente", callback_data=f"{callback_prefix}_done")])
    return InlineKeyboardMarkup(keyboard)

def get_urinary_symptoms_keyboard(selected: set = None):
    """Crea un teclado de checklist para los síntomas urinarios."""
    if selected is None:
        selected = set()

    symptoms = {
        "dolor": "Dolor ",
        "ardor": "Ardor"
    }

    keyboard = []
    for key, text in symptoms.items():
        prefix = "✅ " if key in selected else ""
        keyboard.append([InlineKeyboardButton(f"{prefix}{text}", callback_data=f"urinary_{key}")])

    keyboard.append([InlineKeyboardButton("➡️ Terminar y Siguiente", callback_data="urinary_done")])
    return InlineKeyboardMarkup(keyboard)

def get_yes_no_keyboard(callback_prefix: str):
    """Crea un teclado genérico de Sí/No."""
    keyboard = [
        [
            InlineKeyboardButton("👍 Sí", callback_data=f"{callback_prefix}_yes"),
            InlineKeyboardButton("👎 No", callback_data=f"{callback_prefix}_no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_family_history_keyboard(selected: set = None):
    """Crea un teclado de checklist para antecedentes familiares."""
    if selected is None: selected = set()
    options = {
        "diabetes": "Diabetes",
        "tiroides": "Tiroides",
        "asma": "Asma",
        "alergias": "Alergias",
        "inmunologicas": "Enfermedades Inmunológicas",
        "cardiovasculares": "Enfermedades Cardiovasculares",
        "respiratorias": "Enfermedades Respiratorias",
        "renales": "Enfermedades Renales",
        "intestino_irritable": "Síndrome de Intestino Irritable"
    }
    keyboard = []
    for key, text in options.items():
        prefix = "✅ " if key in selected else ""
        keyboard.append([InlineKeyboardButton(f"{prefix}{text}", callback_data=f"family_{key}")])
    keyboard.append([InlineKeyboardButton("✍️ Otro (escribir)", callback_data="family_other")])
    keyboard.append([InlineKeyboardButton("➡️ Siguiente", callback_data="family_done")])
    return InlineKeyboardMarkup(keyboard)

def get_pathologies_keyboard(callback_prefix: str, selected: set = None):
    """Crea un teclado de checklist genérico para patologías de base."""
    if selected is None:
        selected = set()

    options = {
        "diabetes": "Diabetes",
        "tiroides": "Tiroides",
        "asma": "Asma",
        "alergias": "Alergias",
        "inmunologicas": "Enfermedades Inmunológicas",
        "cardiovasculares": "Enfermedades Cardiovasculares",
        "respiratorias": "Enfermedades Respiratorias",
        "renales": "Enfermedades Renales",
        "intestino_irritable": "Síndrome de Intestino Irritable"
    }

    keyboard = []
    for key, text in options.items():
        prefix = "✅ " if key in selected else ""
        keyboard.append([InlineKeyboardButton(f"{prefix}{text}", callback_data=f"{callback_prefix}_{key}")])

    keyboard.append([InlineKeyboardButton("✍️ Otro (escribir)", callback_data=f"{callback_prefix}_other")])
    keyboard.append([InlineKeyboardButton("➡️ Siguiente", callback_data=f"{callback_prefix}_done")])
    return InlineKeyboardMarkup(keyboard)

def get_bowel_habit_keyboard(selected: set = None):
    """Crea un teclado para los síntomas evacuatorios."""
    if selected is None: selected = set()
    symptoms = {
        "pain": "Dolor al evacuar",
        "bleeding": "Sangrado al evacuar",
        "constipation": "Estreñimiento",
        "bloating": "Distensión abdominal (gases)"
    }
    keyboard = []
    for key, text in symptoms.items():
        prefix = "✅ " if key in selected else ""
        keyboard.append([InlineKeyboardButton(f"{prefix}{text}", callback_data=f"bowel_{key}")])

    none_prefix = "✅ " if "none" in selected else ""
    keyboard.append([InlineKeyboardButton(f"{none_prefix}Ninguno de los anteriores", callback_data="bowel_none")])
    keyboard.append([InlineKeyboardButton("➡️ Terminar y Siguiente", callback_data="bowel_done")])

    return InlineKeyboardMarkup(keyboard)
def get_alcohol_habit_keyboard() -> InlineKeyboardMarkup:
    """Crea un teclado para la pregunta sobre el consumo de alcohol."""
    keyboard = [
        [
            InlineKeyboardButton("👍 Sí", callback_data="habits_alcohol_yes"),
            InlineKeyboardButton("👎 No", callback_data="habits_alcohol_no")
        ],
        [
            InlineKeyboardButton("🥂 Ocasional", callback_data="habits_alcohol_occasional")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_complications_keyboard(callback_prefix: str, selected: set = None) -> InlineKeyboardMarkup:
    """Crea un teclado de checklist para las complicaciones del parto."""
    if selected is None:
        selected = set()

    complications = {
        "preeclampsia": "Preclamsia",
        "diabetes": "Diabetes Gestacional",
        "hemorrhage": "Hemorragia",
        "infection": "Infección",
        "premature": "Parto Prematuro",
        "malformation": "Malformación Congénita"
    }

    keyboard = []
    options_items = list(complications.items())
    for i in range(0, len(options_items), 2):
        row = []
        key1, text1 = options_items[i]
        prefix1 = "✅ " if key1 in selected else ""
        row.append(InlineKeyboardButton(f"{prefix1}{text1}", callback_data=f"{callback_prefix}_{key1}"))

        if i + 1 < len(options_items):
            key2, text2 = options_items[i+1]
            prefix2 = "✅ " if key2 in selected else ""
            row.append(InlineKeyboardButton(f"{prefix2}{text2}", callback_data=f"{callback_prefix}_{key2}"))
        keyboard.append(row)


    keyboard.append([InlineKeyboardButton("➡️ Terminar y Siguiente", callback_data=f"{callback_prefix}_done")])
    return InlineKeyboardMarkup(keyboard)
'''
def get_birth_type_keyboard() -> InlineKeyboardMarkup:
    """Crea un teclado para seleccionar el tipo de nacimiento (Parto o Cesárea)."""
    keyboard = [[
        InlineKeyboardButton("🤱 Parto", callback_data="birth_type_parto"),
        InlineKeyboardButton("🔪 Cesárea", callback_data="birth_type_cesarea")
    ]]
    return InlineKeyboardMarkup(keyboard)'''

