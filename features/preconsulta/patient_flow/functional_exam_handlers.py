# features/preconsulta/functional_exam_handlers.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from features.preconsulta.components import keyboards
#from .gyn_history_handlers import ask_fum
from .habits_handlers import ask_habits_start, finish_preconsultation
from features.preconsulta.states import *

logger = logging.getLogger(__name__)

# --- ESTADOS PARA ESTE MÓDULO ---
"""(
    AWAITING_SEXUAL_PAIN_BOOL, AWAITING_SEXUAL_PAIN_TYPE, AWAITING_SEXUAL_PAIN_SCALE,
    AWAITING_LEG_PAIN_BOOL, AWAITING_LEG_PAIN_TYPE, AWAITING_LEG_PAIN_ZONE,
    AWAITING_GASTRO_BEFORE_BOOL, AWAITING_GASTRO_BEFORE_CHECKLIST,
    AWAITING_GASTRO_DURING_BOOL, AWAITING_GASTRO_DURING_CHECKLIST,
    AWAITING_BOWEL_DISCHEZIA_BOOL, AWAITING_BOWEL_DISCHEZIA_SCALE, AWAITING_BOWEL_FREQUENCY,
    AWAITING_URINARY_PROBLEM_BOOL, AWAITING_URINARY_PAIN_BOOL, AWAITING_URINARY_PAIN_SCALE,
    AWAITING_URINARY_IRRITATION, AWAITING_URINARY_INCONTINENCE, AWAITING_URINARY_NOCTURIA,
) = range(38, 57)"""

# --- INICIO DEL MÓDULO: EXAMEN FUNCIONAL ---

async def ask_functional_exam_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Función de entrada al módulo. Pregunta por Dispareunia."""
    if update.callback_query: await update.callback_query.answer()
    question_text = (
        "**Paso 4: Examen Funcional**\n\n"
        "Ahora, algunas preguntas sobre síntomas específicos.\n\n"
        "¿Presentas dolor al tener relaciones sexuales (Dispareunia)?"
    )
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
        text=question_text, reply_markup=keyboards.get_yes_no_keyboard('sexual_pain_bool')
    )
    return AWAITING_SEXUAL_PAIN_BOOL

async def handle_sexual_pain_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['sexual_pain_dyspareunia'] = "Sí" if query.data.endswith('_yes') else "No"
    if query.data.endswith('_yes'):
        await query.edit_message_text(text="El dolor al momento de la relación sexual es:", reply_markup=keyboards.get_sexual_pain_type_keyboard())
        return AWAITING_SEXUAL_PAIN_TYPE
    else:
        context.user_data['sexual_pain_type'] = 'N/A'
        context.user_data['sexual_pain_scale'] = 'N/A'
        return await ask_leg_pain_bool(update, context)

async def handle_sexual_pain_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    pain_type = query.data.split('_')[-1]
    context.user_data['sexual_pain_type'] = pain_type.capitalize()
    if pain_type == 'profunda':
        await query.edit_message_text(
            text="En una escala del 0 al 10, ¿qué tan intenso es el dolor profundo?",
            reply_markup=keyboards.get_pain_scale_keyboard())
        return AWAITING_SEXUAL_PAIN_SCALE
    else:
        context.user_data['sexual_pain_scale'] = 'N/A'
        return await ask_leg_pain_bool(update, context)



async def handle_sexual_pain_scale(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    scale = query.data.split('_')[-1]
    context.user_data['sexual_pain_scale'] = scale
    return await ask_leg_pain_bool(update, context)

# --- FLUJO DE DOLOR EN PIERNAS ---

async def ask_leg_pain_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query: await update.callback_query.answer()
    question_text = "¿Presentas dolor en miembros inferiores (piernas) durante la menstruación?"
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
        text=question_text, reply_markup=keyboards.get_yes_no_keyboard('leg_pain_bool'))
    return AWAITING_LEG_PAIN_BOOL

async def handle_leg_pain_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data.endswith('_yes'):
        context.user_data['leg_pain_types'] = set()
        await query.edit_message_text(text="Describe cómo es el dolor:", reply_markup=keyboards.get_leg_pain_type_keyboard())
        return AWAITING_LEG_PAIN_TYPE
    else: # Si no hay dolor, saltamos todo el sub-flujo
        context.user_data['leg_pain_type'] = "No"
        context.user_data['leg_pain_zone'] = "N/A"

        # --- ¡CORRECCIÓN #1 - AÑADIR AWAIT! ---
        return await ask_gastro_before_bool(update, context)

async def ask_gastro_before_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query: await update.callback_query.answer()
    question_text = "¿Presentas síntomas gastrointestinales **antes** de la menstruación?"
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
        text=question_text, reply_markup=keyboards.get_yes_no_keyboard('gastro_before_bool'))
    return AWAITING_GASTRO_BEFORE_BOOL

async def handle_leg_pain_type_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selection = query.data.split('_', 3)[-1]
    if selection == 'done':
        types_set = context.user_data.get('leg_pain_types', set())
        context.user_data['leg_pain_type'] = ", ".join(sorted(list(types_set))) if types_set else "Sí, no especificado"
        context.user_data['leg_pain_zones'] = set()
        await query.edit_message_text(text="Ahora por favor indica la zona del dolor de tus piernas:", reply_markup=keyboards.get_leg_pain_zone_keyboard())
        return AWAITING_LEG_PAIN_ZONE
    symptoms = context.user_data.get('leg_pain_types', set())
    if selection in symptoms: symptoms.remove(selection)
    else: symptoms.add(selection)
    try:
        await query.edit_message_reply_markup(reply_markup=keyboards.get_leg_pain_type_keyboard(selected=symptoms))
    except BadRequest as e:
        if "Message is not modified" not in str(e): logger.error(f"Error al actualizar teclado dolor piernas: {e}")
    return AWAITING_LEG_PAIN_TYPE

async def handle_leg_pain_zone_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la checklist de la zona del dolor."""
    query = update.callback_query
    await query.answer()
    selection = query.data.split('_', 3)[-1]

    if selection == 'done':
        zones_set = context.user_data.get('leg_pain_zones', set())
        context.user_data['leg_pain_zone'] = ", ".join(sorted(list(zones_set))) if zones_set else "No especificado"
        # Al terminar, llamamos a la siguiente pregunta (CON AWAIT)
        return await ask_gastro_before_bool(update, context)

    # Lógica de selección/deselección de ítems
    zones = context.user_data.get('leg_pain_zones', set())
    if selection in zones:
        zones.remove(selection)
    else:
        zones.add(selection)

    # Actualizamos el teclado para mostrar el check
    try:
        await query.edit_message_reply_markup(reply_markup=keyboards.get_leg_pain_zone_keyboard(selected=zones))
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error al actualizar teclado zona piernas: {e}")

    # --- ¡CORRECCIÓN CLAVE AQUÍ! ---
    # Después de actualizar el teclado, nos quedamos en el mismo estado
    # para permitir más selecciones.
    return AWAITING_LEG_PAIN_ZONE

async def handle_gastro_before_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja el Sí/No para síntomas gastrointestinales ANTES del periodo."""
    query = update.callback_query
    await query.answer()

    if query.data.endswith('_yes'):
        context.user_data['gastro_before_symptoms'] = set()
        await query.edit_message_text(
            text="Indica cuales de los síntomas presentas:",
            reply_markup=keyboards.get_gastro_symptoms_keyboard('gastro_before')
        )
        return AWAITING_GASTRO_BEFORE_CHECKLIST
    else:
        context.user_data['gastro_symptoms_before_period'] = "No"
        return await ask_gastro_during_bool(update, context) # Pasa a la siguiente pregunta

async def handle_gastro_before_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la checklist de síntomas ANTES del periodo."""
    query = update.callback_query
    await query.answer()
    selection_key = query.data.split('_', 2)[-1]

    # Lógica de "Terminar y Siguiente"
    if selection_key == 'done':
        symptoms_set = context.user_data.get('gastro_before_symptoms', set())

        symptom_map = {
            "nauseas": "Nauseas", "vomitos": "Vómitos", "inflamacion": "Inflamación",
            "distension": "Distensión abdominal", "dolor_evacuar": "Dolor al evacuar",
            "colicos": "Cólicos", "flatulencias": "Flatulencias"
        }

        if symptoms_set:
            translated_symptoms = [symptom_map[key] for key in sorted(list(symptoms_set))]
            symptoms_text = ", ".join(translated_symptoms)
            final_response = f"Presenta síntomas no cíclicos: {symptoms_text}"
        else:
            final_response = "Presenta síntomas no cíclicos: Sí, no especificado"

        context.user_data['gastro_symptoms_before_period'] = final_response
        return await ask_gastro_during_bool(update, context)

    # Lógica de selección/deselección de ítems
    symptoms = context.user_data.get('gastro_before_symptoms', set())
    if selection_key in symptoms:
        symptoms.remove(selection_key)
    else:
        symptoms.add(selection_key)
    context.user_data['gastro_before_symptoms'] = symptoms

    # Actualizar el teclado para mostrar la selección
    try:
        await query.edit_message_reply_markup(
            reply_markup=keyboards.get_gastro_symptoms_keyboard('gastro_before', selected=symptoms)
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error al actualizar teclado gastro (antes): {e}")

    return AWAITING_GASTRO_BEFORE_CHECKLIST

async def ask_gastro_during_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pregunta por los síntomas DURANTE el periodo."""
    query = update.callback_query
    await query.answer()

    question_text = "¿Presentas síntomas gastrointestinales **durante** la menstruación?"
    reply_markup = keyboards.get_yes_no_keyboard('gastro_during_bool')

    await query.edit_message_text(text=question_text, reply_markup=reply_markup)
    return AWAITING_GASTRO_DURING_BOOL

async def handle_gastro_during_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja el Sí/No para síntomas DURANTE el periodo."""
    query = update.callback_query
    await query.answer()

    if query.data.endswith('_yes'):
        context.user_data['gastro_during_symptoms'] = set()
        await query.edit_message_text(
            text="Indica cuales de los síntomas presentas:",
            reply_markup=keyboards.get_gastro_symptoms_keyboard('gastro_during')
        )
        return AWAITING_GASTRO_DURING_CHECKLIST
    else:
        context.user_data['gastro_symptoms_during_period'] = "No"
        # ANTES: handle_bowel_habit_answer. AHORA: ask_urinary_habit_bool
        # Como 'dolor al evacuar' ya está en la checklist, podemos omitir la pregunta de 'hábito evacuatorio'
        return await ask_urinary_problem_bool(update, context)

async def handle_gastro_during_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la checklist de síntomas DURANTE el periodo."""
    query = update.callback_query
    await query.answer()
    selection_key = query.data.split('_', 2)[-1]

    if selection_key == 'done':
        symptoms_set = context.user_data.get('gastro_during_symptoms', set())
        symptom_map = {
            "nauseas": "Nauseas", "vomitos": "Vómitos", "inflamacion": "Inflamación",
            "distension": "Distensión abdominal", "dolor_evacuar": "Dolor al evacuar",
            "colicos": "Cólicos", "flatulencias": "Flatulencias"
        }
        if symptoms_set:
            translated_symptoms = [symptom_map.get(key, key) for key in sorted(list(symptoms_set))]
            symptoms_text = ", ".join(translated_symptoms)
            final_response = f"Manifiesta síntomas cíclicos: {symptoms_text}"
        else:
            final_response = "Manifiesta síntomas cíclicos: Sí, no especificado"
        context.user_data['gastro_symptoms_during_period'] = final_response

        # --- El flujo continúa hacia el nuevo paso de hábito evacuatorio ---
        return await ask_bowel_dischezia(update, context)

    # Lógica de selección/deselección de ítems
    symptoms = context.user_data.get('gastro_during_symptoms', set())
    if selection_key in symptoms:
        symptoms.remove(selection_key)
    else:
        symptoms.add(selection_key)
    context.user_data['gastro_during_symptoms'] = symptoms

    # Actualizar el teclado para mostrar la selección
    try:
        await query.edit_message_reply_markup(
            reply_markup=keyboards.get_gastro_symptoms_keyboard('gastro_during', selected=symptoms)
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error al actualizar teclado gastro (durante): {e}")

    return AWAITING_GASTRO_DURING_CHECKLIST

# --- NUEVAS FUNCIONES PARA HÁBITO EVACUATORIO ---

async def ask_bowel_dischezia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="¿Tienes dolor para evacuar (Disquecia)?",
        reply_markup=keyboards.get_dischezia_keyboard()
    )
    return AWAITING_BOWEL_DISCHEZIA_BOOL

async def handle_bowel_dischezia_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    response = query.data.split('_')[-1]
    response_map = {"yes": "Sí", "no": "No", "eventual": "Eventual"}
    context.user_data['bowel_dischezia'] = response_map.get(response, response)

    if response in ['yes', 'eventual']:
        await query.edit_message_text(
            text="En una escala del 0 al 10, ¿qué tan intenso es el dolor al evacuar?",
            reply_markup=keyboards.get_pain_scale_keyboard()
        )
        return AWAITING_BOWEL_DISCHEZIA_SCALE
    else: # Es 'No'
        context.user_data['bowel_dischezia_scale'] = 'N/A'
        return await ask_bowel_frequency(update, context)

async def handle_bowel_dischezia_scale(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    scale = query.data.split('_')[-1]
    context.user_data['bowel_dischezia_scale'] = scale
    return await ask_bowel_frequency(update, context)

async def ask_bowel_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.answer()
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text="¿Cuál es tu hábito evacuatorio (frecuencia)?",
        reply_markup=keyboards.get_bowel_frequency_keyboard()
    )
    return AWAITING_BOWEL_FREQUENCY

async def handle_bowel_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # --- ¡LÓGICA CORREGIDA AQUÍ! ---
    # 1. Creamos un diccionario para mapear el callback_data completo a su texto.
    frequency_map = {
        "bowel_freq_Diario": "Diario",
        "bowel_freq_Cada 2 días": "Cada 2 días",
        "bowel_freq_Cada 3 días": "Cada 3 días",
        "bowel_freq_Cada 4 días": "Cada 4 días",
        "bowel_freq_Cada 5 días": "Cada 5 días",
        "bowel_freq_Semanal": "Semanal"
    }

    # 2. Obtenemos el texto correcto usando el diccionario.
    frequency_text = frequency_map.get(query.data, "No especificado")

    context.user_data['bowel_frequency'] = frequency_text

    # Continuamos al flujo urinario
    return await ask_urinary_problem_bool(update, context)
# --- FLujo de Hábito Urinario (ya estaba bien, lo incluyo para asegurar) ---

async def ask_urinary_problem_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pregunta inicial: ¿Presentas algún problema al orinar?"""
    if update.callback_query: await update.callback_query.answer()
    question_text = "¿Presentas algún problema al orinar?"
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=question_text,
        reply_markup=keyboards.get_yes_no_keyboard('urinary_problem_bool')
    )
    return AWAITING_URINARY_PROBLEM_BOOL

async def handle_urinary_problem_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data.endswith('_yes'):
        # Si hay problemas, iniciamos el interrogatorio detallado
        await query.edit_message_text(
            text="¿Tienes dolor para orinar?",
            reply_markup=keyboards.get_yes_no_keyboard('urinary_pain_bool')
        )
        return AWAITING_URINARY_PAIN_BOOL
    else:
        # Si no hay problemas, guardamos "Conservado" y saltamos al final
        context.user_data['habits_urinary'] = "Conservado"
        # Limpiamos los otros campos por si acaso
        context.user_data['urinary_pain_scale'] = 'N/A'
        context.user_data['urinary_irritation'] = 'No'
        context.user_data['urinary_incontinence'] = 'No'
        context.user_data['urinary_nocturia'] = 'No'
        return await ask_reason_for_visit(update, context)

async def handle_urinary_pain_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data.endswith('_yes'):
        # Mostramos la escala de dolor
        question_text = "En una escala del 0 al 10, ¿qué tan intenso es el dolor?"
        await query.edit_message_text(
            text=question_text,
            reply_markup=keyboards.get_pain_scale_keyboard()
        )
        return AWAITING_URINARY_PAIN_SCALE
    else:
        # No hay dolor, guardamos N/A y continuamos
        context.user_data['urinary_pain_scale'] = 'N/A'
        return await ask_urinary_irritation(update, context)

async def handle_urinary_pain_scale(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    scale = query.data.split('_')[-1]
    context.user_data['urinary_pain_scale'] = scale
    return await ask_urinary_irritation(update, context)

async def ask_urinary_irritation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="¿Presentas irritación constante al orinar?",
        reply_markup=keyboards.get_yes_no_keyboard('urinary_irritation')
    )
    return AWAITING_URINARY_IRRITATION

async def handle_urinary_irritation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['urinary_irritation'] = "Sí" if query.data.endswith('_yes') else "No"
    await query.edit_message_text(
        text="¿Presentas escape de Orina?",
        reply_markup=keyboards.get_yes_no_keyboard('urinary_incontinence')
    )
    return AWAITING_URINARY_INCONTINENCE

async def handle_urinary_incontinence(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['urinary_incontinence'] = "Sí" if query.data.endswith('_yes') else "No"
    await query.edit_message_text(
        text="Mientras duermes por la noche, ¿te despiertas más de 3 veces para orinar?",
        reply_markup=keyboards.get_yes_no_keyboard('urinary_nocturia')
    )
    return AWAITING_URINARY_NOCTURIA

async def handle_urinary_nocturia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['urinary_nocturia'] = "Sí" if query.data.endswith('_yes') else "No"

    # --- ¡CONEXIÓN FINAL! ---
    # Al terminar el examen funcional, pasamos al módulo de hábitos.
    return await ask_habits_start(update, context)