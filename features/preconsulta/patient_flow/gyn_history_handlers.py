# features/preconsulta/gyn_history_handlers.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest
from features.preconsulta.components import keyboards
from features.preconsulta.components.calendar import FUMCalendar
from .functional_exam_handlers import ask_functional_exam_start
from common import texts
from features.preconsulta.states import *
logger = logging.getLogger(__name__)

# Estados para este módulo (19 estados)

def get_ordinal(number: int) -> str:
    ordinals = ["primer", "segundo", "tercer", "cuarto", "quinto", "sexto", "séptimo", "octavo", "noveno", "décimo"]
    return ordinals[number - 1] if 1 <= number <= 10 else f"{number}º"

async def ask_gyn_history_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Función de entrada al módulo. Ahora pregunta primero por el tipo de consulta."""
    if update.callback_query:
        await update.callback_query.answer()

    question_text = (
        f"{texts.get_text('preconsulta.section_gyn_history')}\n\n"
        f"{texts.get_text('preconsulta.ask_consultation_type')}"
    )
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=question_text,
        reply_markup=keyboards.get_consultation_type_keyboard(),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_CONSULTATION_TYPE

async def handle_consultation_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    consult_type = query.data.split('_')[-1]

    if consult_type == 'gyn':
        context.user_data['consultation_type'] = "Ginecológica"
        await query.edit_message_text(
            text=texts.get_text('preconsulta.ask_gyn_reason'),
            reply_markup=keyboards.get_gyn_reason_keyboard(),
            parse_mode=ParseMode.HTML
        )
        return AWAITING_GYN_CONSULT_REASON
    else: # Es 'prenatal'
        context.user_data['consultation_type'] = "Prenatal"
        context.user_data['reason_for_visit'] = "Control Prenatal"
        # Si es prenatal, podemos saltar la razón y pasar directamente a la historia
        return await ask_gyn_menarche(update, context)

async def ask_gyn_menarche(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pregunta por la Menarquia."""
    if update.callback_query:
        await update.callback_query.answer()

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=texts.get_text('preconsulta.ask_menarche'),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_GYN_MENARCHE

async def handle_gyn_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    reason = query.data.replace('gyn_reason_', '').replace('_', ' ')
    context.user_data['reason_for_visit'] = reason
    return await ask_gyn_menarche(update, context)

async def receive_gyn_menarche(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['gyn_menarche'] = update.message.text
    await update.message.delete()

    # Después de menarquia, continuamos con sexarquia.
    return await ask_gyn_sexarche(update, context)

async def ask_pregnancy_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pregunta si la paciente ha estado embarazada."""
    # Respondemos al query si venimos de un botón
    if update.callback_query:
        await update.callback_query.answer()

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=texts.get_text('preconsulta.ask_pregnancy_bool'),
        reply_markup=keyboards.get_yes_no_keyboard('gyn_pregnancy_bool'),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_GYN_PREGNANCY_BOOL
async def handle_pregnancy_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data.endswith('_yes'):
        # Si sí ha estado embarazada, iniciamos el flujo de Gesta, Partos, etc.
        await query.edit_message_text(text=texts.get_text('preconsulta.ask_gesta'), parse_mode=ParseMode.HTML)
        return AWAITING_GYN_GESTA_NUM
    else:
        # Si no, guardamos Nuligesta...
        context.user_data['gyn_ho'] = "Nuligesta"
        # ... y ANTES de preguntar por la fertilidad, preguntamos si es activa sexualmente.
        # ESTA PARTE DEL FLUJO ESTABA ROTA.
        # El flujo correcto es: ¿Embarazada? -> No -> ¿Activa sexualmente? -> ¿Intención de fertilidad?
        return await ask_sexually_active(update, context)

async def receive_gesta_num(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        gesta = int(update.message.text)
        context.user_data['gyn_gesta'] = gesta
        await update.message.delete()
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
            text=texts.get_text('preconsulta.ask_para'), parse_mode=ParseMode.HTML)
        return AWAITING_GYN_PARA_NUM
    except ValueError:
        await update.message.reply_text(texts.get_text('preconsulta.generic_error_number'))
        return AWAITING_GYN_GESTA_NUM

async def receive_para_num(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        para = int(update.message.text)
        context.user_data['gyn_para'] = para
        await update.message.delete()

        gesta = context.user_data.get('gyn_gesta', 0)

        # --- LÓGICA CORREGIDA ---
        if gesta == para:
            context.user_data['gyn_cesarean'] = 0
            context.user_data['gyn_abortion'] = 0

            # Ahora, en lugar de saltar a fertilidad, verificamos si hay nacimientos.
            total_nacimientos = para # En este caso, solo hay partos
            if total_nacimientos > 0:
                context.user_data['children_details'] = []
                context.user_data['current_child_index'] = 1
                return await ask_child_weight(update, context) # Inicia el bucle
            else:
                return await ask_fertility_intent(update, context) # Continúa normal si no hay nacimientos
        else:
            # El flujo normal si gesta != para
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
                text=texts.get_text('preconsulta.ask_cesarean'), parse_mode=ParseMode.HTML)
            return AWAITING_GYN_CESAREAN_NUM

    except ValueError:
        await update.message.reply_text(texts.get_text('preconsulta.generic_error_number'))
        return AWAITING_GYN_PARA_NUM

async def receive_cesarean_num(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        cesarean = int(update.message.text)
        context.user_data['gyn_cesarean'] = cesarean
        await update.message.delete()

        gesta = context.user_data.get('gyn_gesta', 0)
        para = context.user_data.get('gyn_para', 0)

        # --- LÓGICA CORREGIDA ---
        if gesta == (para + cesarean):
            context.user_data['gyn_abortion'] = 0

            # Verificamos si hay nacimientos antes de saltar.
            total_nacimientos = para + cesarean
            if total_nacimientos > 0:
                context.user_data['children_details'] = []
                context.user_data['current_child_index'] = 1
                return await ask_child_weight(update, context) # Inicia el bucle
            else:
                return await ask_fertility_intent(update, context) # Continúa normal
        else:
            # Flujo normal si aún faltan abortos por contar.
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
                text=texts.get_text('preconsulta.ask_abortion'), parse_mode=ParseMode.HTML)
            return AWAITING_GYN_ABORTION_NUM

    except ValueError:
        await update.message.reply_text(texts.get_text('preconsulta.generic_error_number'))
        return AWAITING_GYN_CESAREAN_NUM

async def receive_abortion_num(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        abortion = int(update.message.text)
        context.user_data['gyn_abortion'] = abortion
        await update.message.delete()

        # --- INICIO DEL NUEVO BUCLE DE HIJOS ---
        partos = context.user_data.get('gyn_para', 0)
        cesareas = context.user_data.get('gyn_cesarean', 0)
        total_nacimientos = partos + cesareas

        if total_nacimientos > 0:
            context.user_data['children_details'] = []
            context.user_data['current_child_index'] = 1
            # Iniciamos el bucle preguntando por el primer hijo
            return await ask_child_weight(update, context)
        else:
            # Si no hay nacimientos, continuamos el flujo normal
            return await ask_fertility_intent(update, context)

    except ValueError:
        await update.message.reply_text(texts.get_text('preconsulta.generic_error_number'))
        return AWAITING_GYN_ABORTION_NUM
async def ask_child_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Pregunta el peso del hijo actual."""
    child_index = context.user_data['current_child_index']
    ordinal = get_ordinal(child_index)

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        question_text = f"<b>Para tu **{ordinal}** hijo/a, ¿cuántos **kilogramos** pesó al nacer? Por favor, introduce solo el número (ej: 3.5).</b>",
        parse_mode=ParseMode.HTML
    )
    return AWAITING_CHILD_WEIGHT

async def receive_child_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe el peso, lo valida y pregunta la talla."""
    weight_input = update.message.text.replace(',', '.') # Reemplaza coma por punto para decimales
    child_index = context.user_data['current_child_index']

    await update.message.delete()

    # --- VALIDACIÓN NUMÉRICA ---
    try:
        # Intentamos convertir a float para permitir decimales
        float(weight_input)
    except ValueError:
        # Si falla, enviamos un mensaje de error y nos quedamos en el mismo estado
        # (Usaremos una lógica de error simple por ahora, sin contador de intentos)
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=context.user_data['anchor_message_id'],
            text=f"❌ **Formato incorrecto.**\n\nPara tu **{get_ordinal(child_index)}** hijo/a, introduce el peso solo con números (ej: 3.5).",
            parse_mode=ParseMode.HTML
        )
        return AWAITING_CHILD_WEIGHT

    # Si la validación pasa, guardamos el dato
    if len(context.user_data.get('children_details', [])) < child_index:
        context.user_data.setdefault('children_details', []).append({'child_number': child_index})

    context.user_data['children_details'][child_index - 1]['weight'] = weight_input

    # --- PREGUNTA MODIFICADA ---
    ordinal = get_ordinal(child_index)
    question_text = f"Entendido. Ahora, ¿cuántos **centímetros** midió tu **{ordinal}** hijo/a al nacer? Por favor, introduce solo el número (ej: 50)."

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=question_text,
        parse_mode=ParseMode.HTML
    )
    return AWAITING_CHILD_HEIGHT

async def receive_child_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe la talla, la valida y pregunta el año de nacimiento."""
    height_input = update.message.text
    child_index = context.user_data['current_child_index']

    await update.message.delete()

    # --- VALIDACIÓN NUMÉRICA ---
    if not height_input.isdigit():
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=context.user_data['anchor_message_id'],
            text=f"❌ **Formato incorrecto.**\n\nPara tu **{get_ordinal(child_index)}** hijo/a, introduce la talla solo con números enteros (ej: 50).",
            parse_mode=ParseMode.HTML
        )
        return AWAITING_CHILD_HEIGHT

    # Si la validación pasa, guardamos el dato
    context.user_data['children_details'][child_index - 1]['height'] = height_input

    ordinal = get_ordinal(child_index)
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=f"¿En qué año nació tu **{ordinal}** hijo/a?",
        parse_mode=ParseMode.HTML
    )
    return AWAITING_CHILD_BIRTH_YEAR

async def receive_child_birth_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe el año y AHORA pregunta por el tipo de parto."""
    year = update.message.text
    child_index = context.user_data['current_child_index']
    context.user_data['children_details'][child_index - 1]['birth_year'] = year
    await update.message.delete()

    ordinal = get_ordinal(child_index)
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text=f"¿Cómo nació tu **{ordinal}** hijo/a?", # Nueva pregunta
        reply_markup=keyboards.get_birth_type_keyboard(), # Nuevo teclado
        parse_mode=ParseMode.HTML
    )
    return AWAITING_CHILD_BIRTH_TYPE # Nuevo estado

async def handle_child_birth_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recibe el tipo de parto y pregunta por complicaciones."""
    query = update.callback_query
    await query.answer()

    birth_type = "Parto" if query.data.endswith('_parto') else "Cesárea"
    child_index = context.user_data['current_child_index']
    context.user_data['children_details'][child_index - 1]['birth_type'] = birth_type

    ordinal = get_ordinal(child_index)
    await query.edit_message_text(
        text=f"¿Tuviste alguna complicación en tu **{ordinal}** parto/cesárea?",
        reply_markup=keyboards.get_yes_no_keyboard('complication_bool'),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_CHILD_COMPLICATIONS_BOOL
async def handle_complications_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja Sí/No a complicaciones y avanza."""
    query = update.callback_query
    await query.answer()
    child_index = context.user_data['current_child_index']

    if query.data.endswith('_yes'):
        # Si hubo complicaciones, mostramos la checklist
        context.user_data['children_details'][child_index - 1]['complications_selected'] = set()
        await query.edit_message_text(
            text="Por favor, selecciona las complicaciones que tuviste:",
            reply_markup=keyboards.get_complications_keyboard()
        )
        return AWAITING_CHILD_COMPLICATIONS_CHECKLIST
    else:
        # Si no hubo, guardamos "Ninguna" y pasamos al siguiente hijo o finalizamos el bucle
        context.user_data['children_details'][child_index - 1]['complications'] = "Ninguna"
        return await next_child_or_continue(update, context)

async def handle_complications_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selection = query.data.split('_', 1)[-1]
    child_index = context.user_data['current_child_index']
    selected = context.user_data['children_details'][child_index - 1]['complications_selected']

    if selection == 'done':
        if not selected:
            final_text = "Sí, no especificada"
        else:
            complication_map = {
                "preeclampsia": "Preclamsia", "diabetes": "Diabetes Gestacional", "hemorrhage": "Hemorragia",
                "infection": "Infección", "premature": "Parto Prematuro", "malformation": "Malformación Congénita"
            }
            final_text = ", ".join(complication_map.get(key, key) for key in sorted(list(selected)))
        context.user_data['children_details'][child_index - 1]['complications'] = final_text
        context.user_data['children_details'][child_index - 1].pop('complications_selected')
        return await next_child_or_continue(update, context)

    elif selection == 'other':
        await query.edit_message_text(text="Por favor, escribe la otra complicación:")
        return AWAITING_CHILD_COMPLICATIONS_OTHER

    if selection in selected:
        selected.remove(selection)
    else:
        selected.add(selection)

    await query.edit_message_reply_markup(reply_markup=keyboards.get_complications_keyboard(selected=selected))
    return AWAITING_CHILD_COMPLICATIONS_CHECKLIST

async def receive_complication_other_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    other_text = update.message.text
    child_index = context.user_data['current_child_index']
    selected = context.user_data['children_details'][child_index - 1]['complications_selected']
    selected.add(other_text)
    await update.message.delete()

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=context.user_data['anchor_message_id'],
        text="Complicación añadida. Selecciona más o termina:",
        reply_markup=keyboards.get_complications_keyboard(selected=selected)
    )
    return AWAITING_CHILD_COMPLICATIONS_CHECKLIST


async def next_child_or_continue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Función de control del bucle: pasa al siguiente hijo o continúa el flujo."""
    partos = context.user_data.get('gyn_para', 0)
    cesareas = context.user_data.get('gyn_cesarean', 0)
    total_nacimientos = partos + cesareas

    current_child = context.user_data['current_child_index']

    if current_child < total_nacimientos:
        context.user_data['current_child_index'] += 1
        return await ask_child_weight(update, context)
    else:
        context.user_data.pop('current_child_index', None)
        # --- CAMBIO CLAVE ---
        # Al terminar el bucle, la siguiente pregunta es si es activa sexualmente.
        return await ask_sexually_active(update, context)

async def ask_fertility_intent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=texts.get_text('preconsulta.ask_fertility_intent'),
            reply_markup=keyboards.get_fertility_intent_keyboard(),
            parse_mode=ParseMode.HTML
        )
    else:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
            text=texts.get_text('preconsulta.ask_fertility_intent'),
            reply_markup=keyboards.get_fertility_intent_keyboard(),
            parse_mode=ParseMode.HTML
        )
    return AWAITING_GYN_FERTILITY_INTENT

async def handle_fertility_intent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    response_map = {
        "fertility_yes": "Con deseo de fertilidad por más de un año",
        "fertility_no_not_looking": "No tiene deseo de fertilidad",
        "fertility_no_not_planned": "Prefiere no responder"
    }
    fertility_text = response_map.get(query.data)
    if fertility_text:
        context.user_data['gyn_fertility_intent'] = fertility_text

    # --- CAMBIO CLAVE ---
    # Después de la intención de fertilidad, SIEMPRE pasamos a preguntar por los ciclos.
    await query.edit_message_text(
        text=texts.get_text('preconsulta.ask_cycles_regular'),
        reply_markup=keyboards.get_yes_no_keyboard('gyn_cycles_regular'),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_GYN_CYCLES_REGULAR

async def handle_gyn_cycles_regular_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data.endswith('_yes'):
        context.user_data['gyn_cycles'] = "Regulares"
        await query.edit_message_text(
            text=texts.get_text('preconsulta.ask_dismenorrhea_bool'),
            reply_markup=keyboards.get_yes_no_keyboard('gyn_dysmenorrhea_bool'),
            parse_mode=ParseMode.HTML
        )
        return AWAITING_GYN_DYSMENORRHEA_BOOL
    else:
        await query.edit_message_text(text=texts.get_text('preconsulta.ask_cycles_duration'), parse_mode=ParseMode.HTML)
        return AWAITING_GYN_CYCLES_DURATION

async def receive_gyn_cycles_duration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['gyn_cycles_duration'] = update.message.text
    await update.message.delete()
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
        text=texts.get_text('preconsulta.ask_cycles_frequency'), parse_mode=ParseMode.HTML)
    return AWAITING_GYN_CYCLES_FREQUENCY

async def receive_gyn_cycles_frequency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['gyn_cycles_frequency'] = update.message.text
    await update.message.delete()
    duration = context.user_data.get('gyn_cycles_duration', 'N/A')
    frequency = context.user_data.get('gyn_cycles_frequency', 'N/A')
    context.user_data['gyn_cycles'] = f"Irregulares. Duración: {duration}. Frecuencia: {frequency}."
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
        text=texts.get_text('preconsulta.ask_dismenorrhea_bool'),
        reply_markup=keyboards.get_yes_no_keyboard('gyn_dysmenorrhea_bool'),
        parse_mode=ParseMode.HTML
    )
    return AWAITING_GYN_DYSMENORRHEA_BOOL

async def handle_gyn_dysmenorrhea_bool_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data.endswith('_yes'):
        context.user_data['dismenorrhea_temp'] = True
        await query.edit_message_text(
            text=texts.get_text('preconsulta.dismenorrhea_scale_intro'),
            reply_markup=keyboards.get_pain_scale_keyboard(),
            parse_mode=ParseMode.HTML)
        return AWAITING_GYN_DYSMENORRHEA_SCALE
    else:
        context.user_data['gyn_dysmenorrhea'] = "No"
        # --- CAMBIO CLAVE ---
        # Después del dolor, pasamos a la FUM.
        return await ask_fum(update, context)

async def handle_gyn_dysmenorrhea_scale(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    scale = query.data.split('_')[-1]
    if context.user_data.get('dismenorrhea_temp'):
        context.user_data['gyn_dysmenorrhea'] = f"Sí, intensidad: {scale}/10"
    else:
        context.user_data['gyn_dysmenorrhea'] = f"Intensidad: {scale}/10"
    context.user_data.pop('dismenorrhea_temp', None)

    # --- CAMBIO CLAVE ---
    # Después del dolor, pasamos a la FUM.
    return await ask_fum(update, context)

async def ask_gyn_sexarche(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    question_text = texts.get_text('preconsulta.ask_sexarche')
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Nunca he tenido", callback_data="sexarche_never")]])
    if update.callback_query:
        await update.callback_query.edit_message_text(text=question_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
            text=question_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    return AWAITING_GYN_SEXARCHE

async def handle_gyn_sexarche_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query and update.callback_query.data == "sexarche_never":
        query = update.callback_query
        await query.answer()
        context.user_data['gyn_sexarche'] = "Nunca"
    elif update.message:
        context.user_data['gyn_sexarche'] = update.message.text
        await update.message.delete()
    else:
        return AWAITING_GYN_SEXARCHE

    # --- CAMBIO CLAVE ---
    # Después de sexarquia, la siguiente pregunta lógica es sobre embarazos.
    return await ask_pregnancy_bool(update, context)


async def ask_sexually_active(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    question_text = texts.get_text('preconsulta.ask_sexually_active')
    reply_markup = keyboards.get_yes_no_keyboard('sexually_active')
    if update.callback_query:
        await update.callback_query.edit_message_text(text=question_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
            text=question_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    return AWAITING_SEXUALLY_ACTIVE

async def handle_sexually_active_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['sexually_active'] = "Sí" if query.data.endswith('_yes') else "No"

    # --- CAMBIO CLAVE ---
    # Si 'gyn_ho' es 'Nuligesta', significa que respondió "No" a la pregunta de embarazo.
    # En este caso, la siguiente pregunta es sobre la intención de fertilidad.
    if context.user_data.get('gyn_ho') == 'Nuligesta':
        return await ask_fertility_intent(update, context)
    else:
        # Si ya pasó por el flujo de embarazos (o lo saltó), la siguiente pregunta es la FUM.
        return await ask_fertility_intent(update, context)

async def ask_fum(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query: await update.callback_query.answer()
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
        text=texts.get_text('preconsulta.ask_fum'),
        reply_markup=FUMCalendar().create_calendar(),
        parse_mode=ParseMode.HTML)
    return AWAITING_GYN_FUM

async def handle_fum_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("fum_cal_nav_"):
        parts = data.split('_'); year, month = map(int, parts[-1].split('-'))
        await query.message.edit_reply_markup(FUMCalendar().create_calendar(year, month))
        return AWAITING_GYN_FUM
    selected_date = FUMCalendar().process_selection(data)
    if not selected_date: return AWAITING_GYN_FUM
    context.user_data['gyn_fum'] = selected_date.isoformat()
    await query.edit_message_text(
        text=texts.get_text('preconsulta.ask_mac'),
        reply_markup=keyboards.get_yes_no_keyboard('gyn_mac_bool'),
        parse_mode=ParseMode.HTML)
    return AWAITING_GYN_MAC_BOOL

async def handle_gyn_mac_bool(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data.endswith('_yes'):
        context.user_data['mac_selected'] = set()
        await query.edit_message_text(
            text="Selecciona el/los método(s) que usas:",
            reply_markup=keyboards.get_mac_keyboard()
        )
        return AWAITING_GYN_MAC_CHECKLIST
    else:
        context.user_data['gyn_mac'] = "No"
        return await ask_previous_checkups_date(update, context)

async def handle_mac_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    selection = query.data.split('_', 2)[-1]

    if selection == 'done':
        selected_set = context.user_data.get('mac_selected', set())

        # El mapa de traducción ahora vive aquí
        mac_map = {
            "pastillas": "Pastillas", "diu": "DIU", "inyeccion": "Inyección", "implante": "Implante",
            "anillo": "Anillo Vaginal", "parche": "Parche", "condones": "Condones",
            "ritmo": "Método del Ritmo", "coitus_interruptus": "Coitus Interruptus"
        }

        if selected_set:
            translated = [mac_map.get(key, key.capitalize()) for key in sorted(list(selected_set))]
            context.user_data['gyn_mac'] = ", ".join(translated)
        else:
            context.user_data['gyn_mac'] = "Sí, no especificado"

        return await ask_previous_checkups_date(update, context)

    # --- LÓGICA "OTRO" ELIMINADA ---

    selected = context.user_data.get('mac_selected', set())
    if selection in selected:
        selected.remove(selection)
    else:
        selected.add(selection)

    await query.edit_message_reply_markup(reply_markup=keyboards.get_mac_keyboard(selected=selected))
    return AWAITING_GYN_MAC_CHECKLIST

async def ask_previous_checkups_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.callback_query: await update.callback_query.answer()
    question_text = "📅 ¿Cuál es la fecha de tu último control ginecológico?"
    original_calendar = FUMCalendar().create_calendar()
    new_keyboard_rows = [
        [InlineKeyboardButton(button.text, callback_data=button.callback_data.replace('fum_cal_', 'checkup_cal_')) for button in row]
        for row in original_calendar.inline_keyboard
    ]
    new_keyboard_rows.append([InlineKeyboardButton("🚫 Nunca he tenido un control", callback_data="checkup_cal_never")])
    final_markup = InlineKeyboardMarkup(new_keyboard_rows)
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id, message_id=context.user_data['anchor_message_id'],
        text=question_text, reply_markup=final_markup)
    return AWAITING_GYN_PREVIOUS_CHECKUPS_DATE

async def handle_previous_checkups_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "checkup_cal_never":
        context.user_data['gyn_previous_checkups'] = "Nunca"
        return await ask_last_pap_smear_date(update, context)
    if data.startswith("checkup_cal_nav_"):
        parts = data.split('_'); year, month = map(int, parts[-1].split('-'))
        original_calendar = FUMCalendar().create_calendar(year, month)
        new_keyboard_rows = [[InlineKeyboardButton(b.text, callback_data=b.callback_data.replace('fum_cal_', 'checkup_cal_')) for b in r] for r in original_calendar.inline_keyboard]
        new_keyboard_rows.append([InlineKeyboardButton("🚫 Nunca he tenido un control", callback_data="checkup_cal_never")])
        await query.message.edit_reply_markup(InlineKeyboardMarkup(new_keyboard_rows))
        return AWAITING_GYN_PREVIOUS_CHECKUPS_DATE
    selected_date = FUMCalendar().process_selection(data.replace('checkup_cal_', 'fum_cal_'))
    if not selected_date: return AWAITING_GYN_PREVIOUS_CHECKUPS_DATE
    context.user_data['gyn_previous_checkups'] = selected_date.isoformat()
    return await ask_last_pap_smear_date(update, context)

async def ask_last_pap_smear_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    question_text = "📅 ¿Cuál es la fecha de tu última citología?"
    original_calendar = FUMCalendar().create_calendar()
    new_keyboard_rows = [[InlineKeyboardButton(b.text, callback_data=b.callback_data.replace('fum_cal_', 'pap_smear_cal_')) for b in r] for r in original_calendar.inline_keyboard]
    new_keyboard_rows.append([InlineKeyboardButton("🚫 Nunca me he realizado una", callback_data="pap_smear_cal_never")])
    final_markup = InlineKeyboardMarkup(new_keyboard_rows)
    await query.edit_message_text(text=question_text, reply_markup=final_markup)
    return AWAITING_GYN_LAST_PAP_SMEAR_DATE

async def handle_last_pap_smear_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "pap_smear_cal_never":
        context.user_data['gyn_last_pap_smear'] = "Nunca"
        return await ask_functional_exam_start(update, context)
    if data.startswith("pap_smear_cal_nav_"):
        parts = data.split('_'); year, month = map(int, parts[-1].split('-'))
        original_calendar = FUMCalendar().create_calendar(year, month)
        new_keyboard_rows = [[InlineKeyboardButton(b.text, callback_data=b.callback_data.replace('fum_cal_', 'pap_smear_cal_')) for b in r] for r in original_calendar.inline_keyboard]
        new_keyboard_rows.append([InlineKeyboardButton("🚫 Nunca me he realizado una", callback_data="pap_smear_cal_never")])
        await query.message.edit_reply_markup(InlineKeyboardMarkup(new_keyboard_rows))
        return AWAITING_GYN_LAST_PAP_SMEAR_DATE
    selected_date = FUMCalendar().process_selection(data.replace('pap_smear_cal_', 'fum_cal_'))
    if not selected_date: return AWAITING_GYN_LAST_PAP_SMEAR_DATE
    context.user_data['gyn_last_pap_smear'] = selected_date.isoformat()
    return await ask_functional_exam_start(update, context)