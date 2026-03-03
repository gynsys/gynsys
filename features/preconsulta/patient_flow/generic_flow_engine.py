# features/preconsulta/patient_flow/generic_flow_engine.py
import asyncio
import json
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest
from common import texts
from features.preconsulta.states import *
from .flow_actions import text_input, yes_no, checklist, buttons, calendar, loop, scale, loop_inputs, month_year_picker
from ..flow_actions import render as flow_actions_render
from ..flow_actions.router import process_conditional_handler, process_conditional_calc_handler
from .flow_actions import special_checklist
# show_main_menu no existe en el bot nuevo, se usa patient_main_menu desde patient_handler
# from features.main_menu.user_handlers import show_main_menu
from .flow_actions import numeric_keypad
from .flow_actions import year_picker
from .flow_actions import ho_table
from .flow_actions import loop_checklist
from .flow_actions import number_grid
from .flow_actions import sexarche_picker

from database import preconsulta_db
from database.session import get_session
from database.repositories.appointment_repository import AppointmentRepository
from utils.role_manager import RoleManager
from config import DB_PATH
logger = logging.getLogger(__name__)

# Inicializar instancias
role_manager = RoleManager(DB_PATH)


# --- Cargar el Flujo ---
try:
    with open('features/preconsulta/flows/personal_info_flow.json', 'r', encoding='utf-8') as f:
        preconsultation_flow = json.load(f)
except FileNotFoundError:
    logger.error("¡CRÍTICO! No se encontró el archivo de flujo 'personal_info_flow.json'")
    preconsultation_flow = None

# features/preconsulta/patient_flow/generic_flow_engine.py



logger = logging.getLogger(__name__)




async def process_edit_request(update: Update, context: ContextTypes.DEFAULT_TYPE, field_to_edit: str):
    """
    Función auxiliar para manejar un clic en un botón 'Editar'.
    Salta al nodo de la pregunta correspondiente.
    """
    # Mapeo del campo a editar al nodo del flujo que hace la pregunta
    field_to_node_map = {
        'full_name': 'ASK_FULL_NAME',
        'age': 'ASK_AGE',
        'ci': 'ASK_CI',
        'phone': 'ASK_PHONE',
        'address': 'ASK_ADDRESS',
        'occupation': 'ASK_OCCUPATION'
    }

    node_to_jump_to = field_to_node_map.get(field_to_edit)

    if node_to_jump_to:
        # Guardamos en la "memoria" del usuario que estamos en modo edición
        # y que debemos volver al resumen después.
        context.user_data['return_to_node'] = 'SHOW_SUMMARY'
        # Usamos render_node para saltar a la pregunta
        return await render_node(update, context, node_to_jump_to)

    # Si el campo no se encuentra, simplemente nos quedamos esperando
    return AWAITING_GENERIC_INPUT

async def render_message_node(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Muestra un mensaje informativo y continúa al siguiente nodo."""
    text = texts.get_text(node['text_key'], "Información:")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        parse_mode=ParseMode.HTML
    )
    # Pausa breve para que el usuario pueda leer
    await asyncio.sleep(1.5)
    return await render_node(update, context, node['next_node'])

async def render_node(update: Update, context: ContextTypes.DEFAULT_TYPE, node_id: str):
    """Función principal que lee un nodo y despacha al renderizador apropiado."""
    node = context.user_data['flow']['nodes'][node_id]
    context.user_data['current_node_id'] = node_id
    node_type = node.get('type')

    renderers = {
        'text_input': text_input.render,
        'numeric_input': text_input.render,
        'yes_no': yes_no.render,
        'buttons': buttons.render,
        'checklist': checklist.render,

        'loop_text_input': loop_inputs.render_text,
        'loop_numeric_input': loop_inputs.render_text,
        'loop_buttons': loop_inputs.render_buttons,
        'loop_calendar': loop_inputs.render_calendar,
        'year_picker': year_picker.render,
        'ho_table': ho_table.render,
        'message': render_message_node,
        'loop_checklist': loop_checklist.render,
        'number_grid': number_grid.render,
        'sexarche_picker': sexarche_picker.render,
        'numeric_keypad': numeric_keypad.render,
        'month_year_picker': month_year_picker.render,


        'calendar': calendar.render,
        'scale': scale.render, # <-- AÑADIDO
        'special_checklist': special_checklist.render,
        'action': flow_actions_render,
        'conditional': process_conditional_handler,
        'conditional_calc': process_conditional_calc_handler,
    }

    if node_type in renderers:
        return await renderers[node_type](update, context, node)

    logger.error(f"Tipo de nodo desconocido en render_node: {node_type}")
    return ConversationHandler.END



# En features/preconsulta/patient_flow/generic_flow_engine.py

async def process_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Función principal que recibe una entrada del usuario y decide el siguiente paso.
    """
    print("\n" + "="*50)
    print("--- 1. [ENGINE] Iniciando process_input ---")

    # --- Intercepción de acciones especiales ---
    if update.callback_query:
        print(f"--- Callback Data Recibido: {update.callback_query.data} ---")
        query_data = update.callback_query.data
        if query_data.startswith('edit_'):
            field_to_edit = query_data.split('_', 1)[1]
            print(f"--- [ENGINE] Acción especial: EDITAR campo '{field_to_edit}' ---")
            return await process_edit_request(update, context, field_to_edit)

        if query_data.endswith('_continue'):
            await update.callback_query.answer()
            current_node_id = context.user_data.get('current_node_id')
            if not current_node_id:
                logger.error("No se encontró current_node_id al presionar continuar")
                return ConversationHandler.END
            
            node = context.user_data['flow']['nodes'].get(current_node_id)
            if not node:
                logger.error(f"Nodo '{current_node_id}' no encontrado en el flujo")
                return ConversationHandler.END
            
            next_node_id = node.get('next_node')
            print(f"--- [ENGINE] Acción especial: CONTINUAR. Próximo nodo: '{next_node_id}' ---")
            
            if not next_node_id:
                logger.error(f"El nodo '{current_node_id}' no tiene next_node definido")
                return ConversationHandler.END
            
            return await render_node(update, context, next_node_id)

    # --- Lógica de Retorno de Edición ---
    if 'return_to_node' in context.user_data:
        current_node_id = context.user_data.get('current_node_id')
        node = context.user_data['flow']['nodes'][current_node_id]
        node_type = node.get('type')
        print(f"--- [ENGINE] MODO EDICIÓN detectado. Nodo actual: '{current_node_id}' ---")

        if node_type in ['text_input', 'numeric_input'] and update.message and update.message.text:
            user_input = update.message.text
            await update.message.delete()
            if 'save_to' in node:
                context.user_data[node['save_to']] = user_input
            node_to_return_to = context.user_data.pop('return_to_node')
            print(f"--- [ENGINE] Texto editado guardado. Volviendo a '{node_to_return_to}' ---")
            return await render_node(update, context, node_to_return_to)

        elif node_type == 'numeric_keypad' and update.callback_query:
            await numeric_keypad.process(update, context, node)
            if update.callback_query.data.endswith('_submit'):
                node_to_return_to = context.user_data.pop('return_to_node')
                print(f"--- [ENGINE] Keypad finalizado. Volviendo a '{node_to_return_to}' ---")
                return await render_node(update, context, node_to_return_to)
            else:
                print("--- [ENGINE] Clic en keypad (no submit). Esperando... ---")
                return AWAITING_GENERIC_INPUT

    # --- Lógica normal del motor ---
    current_node_id = context.user_data.get('current_node_id')
    print(f"--- 2. [ENGINE] Nodo actual es: '{current_node_id}' ---")

    if not current_node_id:
        print("--- [ENGINE] ERROR: No hay nodo actual. Terminando.")
        return ConversationHandler.END

    node = context.user_data['flow']['nodes'][current_node_id]
    node_type = node.get('type')
    print(f"--- 3. [ENGINE] Tipo de nodo es: '{node_type}' ---")
    next_node_id = None

    processors = {
        'text_input': text_input.process, 'numeric_input': text_input.process,
        'yes_no': yes_no.process, 'buttons': buttons.process, 'checklist': checklist.process,
        'calendar': calendar.process, 'scale': scale.process, 'special_checklist': special_checklist.process, 'loop_checklist': loop_checklist.process,
        'loop_text_input': loop_inputs.process_text_in_loop,
        'loop_numeric_input': loop_inputs.process_text_in_loop,
        'loop_buttons': loop_inputs.process_buttons_in_loop,
        'loop_calendar': loop_inputs.process_calendar_in_loop,
        'year_picker': year_picker.process,
        'ho_table': ho_table.process,
        'number_grid': number_grid.process, 'sexarche_picker': sexarche_picker.process, 'numeric_keypad': numeric_keypad.process, 'month_year_picker': month_year_picker.process
    }

    print(f"--- 4. [ENGINE] Buscando un procesador para el tipo '{node_type}' ---")
    is_text_update = update.message and update.message.text
    is_callback_update = update.callback_query

    node_expects_text = node_type in ['text_input', 'numeric_input', 'loop_text_input', 'loop_numeric_input']
    node_expects_callback = node_type in ['yes_no', 'buttons', 'numeric_keypad', 'checklist', 'calendar', 'scale', 'loop_buttons', 'loop_calendar', 'special_checklist', 'year_picker', 'ho_table', 'loop_checklist', 'number_grid', 'sexarche_picker', 'month_year_picker' ]

    if (node_expects_text and is_text_update) or (node_expects_callback and is_callback_update):
        if node_type in processors:
            print(f"--- 5. [ENGINE] Procesador encontrado. Llamando a '{processors[node_type].__module__}.{processors[node_type].__name__}'... ---")
            next_node_id = await processors[node_type](update, context, node)
            print(f"--- 6. [ENGINE] El procesador devolvió: '{next_node_id}' (Tipo: {type(next_node_id)}) ---")
        else:
            print(f"--- [ENGINE] WARNING: No se encontró procesador para el tipo '{node_type}'. ---")
    else:
        print(f"--- [ENGINE] WARNING: Tipo de update no coincide con el esperado por el nodo. Se ignora la entrada. ---")
        if is_callback_update: await update.callback_query.answer("Acción no válida en este paso.", show_alert=True)
        return AWAITING_GENERIC_INPUT

    # --- Lógica de Transición ---

    # CASO 1: La acción/procesador devolvió un ESTADO (ej. AWAITING_CHECKLIST_OTHER)
    if isinstance(next_node_id, int):
        print(f"--- 7. [ENGINE] El procesador devolvió un ESTADO: {next_node_id}. Transicionando estado. ---")
        return next_node_id

    # CASO 2: El procesador devolvió un ID DE NODO (str) para continuar
    if next_node_id:
        print(f"--- 7. [ENGINE] Hay un próximo nodo. Transicionando a '{next_node_id}'... ---")
        return await render_node(update, context, next_node_id)

    # CASO 3: El procesador devolvió None (nos quedamos esperando en el mismo paso)
    print(f"--- 8. [ENGINE] No hay próximo nodo (o es None). La conversación espera en AWAITING_GENERIC_INPUT. ---")
    print("="*50 + "\n")
    return AWAITING_GENERIC_INPUT

async def start_preconsultation_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Inicia la preconsulta, cargando primero el contexto de la cita agendada
    y luego mostrando la introducción y la primera pregunta.
    """
    if not preconsultation_flow:
        if update.callback_query: await update.callback_query.answer()
        await context.bot.send_message(update.effective_chat.id, "Error crítico: No se pudo cargar el flujo de la preconsulta.")
        return ConversationHandler.END

    query = update.callback_query
    
    # 1. Obtener doctor_id y appointment_id
    appointment_id = None
    doctor_id = None
    
    if query:
        await query.answer()
        try:
            # Extraemos el ID de la cita del callback_data (ej. "preconsulta_start_123")
            appointment_id = int(query.data.split('_')[-1])
        except (ValueError, IndexError):
            await query.message.edit_text("Error: No se pudo identificar la cita para esta preconsulta.")
            return ConversationHandler.END
        
        # En el flujo por botón, el doctor_id suele estar en user_data o lo buscamos
        doctor_id = context.user_data.get('doctor_id')
    else:
        # Si venimos de un Comando (/start preconsult_1)
        if context.args and context.args[0].startswith('preconsult_'):
            try:
                doctor_id = int(context.args[0].split('_')[1])
                # Guardamos en context para el resto del flujo
                context.user_data['doctor_id'] = doctor_id
            except (ValueError, IndexError):
                pass
        
        if not doctor_id:
            doctor_id = context.user_data.get('doctor_id')

    # 2. Asegurar doctor_id y asignación
    user_id = update.effective_user.id
    if not doctor_id:
        assigned_doctor = await role_manager.get_assigned_doctor(user_id)
        if not assigned_doctor:
            error_msg = "Error: No se pudo identificar tu médico."
            if query: await query.message.edit_text(error_msg)
            else: await context.bot.send_message(update.effective_chat.id, error_msg)
            return ConversationHandler.END
        doctor_id = assigned_doctor[0]
    
    # Auto-asignar paciente al médico si es necesario (especialmente para deep links)
    await role_manager.assign_patient_to_doctor(user_id, doctor_id)
    
    # 3. Obtener appointment_id si no lo tenemos (para deep links)
    if not appointment_id:
        appointment_id = context.user_data.get('appointment_id')
        
    # Si sigue siendo None, intentamos buscar la más reciente
    if not appointment_id:
        async with get_session() as session:
            appt_repo = AppointmentRepository(session)
            appt = await appt_repo.get_latest_appointment_for_patient(user_id, doctor_id)
            if appt:
                appointment_id = appt['id']

    # 4. Obtener datos de la cita
    appointment_data = None
    if appointment_id:
        async with get_session() as session:
            appointment_repo = AppointmentRepository(session)
            appointment_data = await appointment_repo.get_appointment_by_id(appointment_id, doctor_id)

    # Solo limpiar si no venimos de deep link (donde ya pusimos el appointment_id)
    if query:
        context.user_data.clear() 

    # Si no hay cita (deep link directo), usamos valores por defecto
    if not appointment_data:
        appointment_dict = {
            'consultation_type': 'Ginecología', # Default razonable
            'is_first_pregnancy': False,
            'has_been_pregnant': False,
            'reason': 'Consulta Directa (Sin Cita)'
        }
    else:
        # Convertir sqlite3.Row a dict
        if hasattr(appointment_data, 'keys'):
            appointment_dict = dict(appointment_data)
        else:
            appointment_dict = appointment_data

    logger.info(f"Iniciando preconsulta para cita #{appointment_id} con doctor_id {doctor_id}...")
    # Poblamos el contexto con los datos importantes de la cita
    context.user_data['appointment_id'] = appointment_id
    context.user_data['doctor_id'] = doctor_id  # Guardar doctor_id para multi-tenant
    context.user_data['consultation_type'] = appointment_dict.get('consultation_type')
    context.user_data['is_first_pregnancy'] = appointment_dict.get('is_first_pregnancy')
    context.user_data['has_been_pregnant'] = appointment_dict.get('has_been_pregnant')
    context.user_data['reason_for_visit'] = appointment_dict.get('reason')
    # --- FIN DE LA LÓGICA DE CARGA DE CONTEXTO ---
    print("\n" + "="*20 + " CONTEXTO CARGADO AL INICIAR PRECONSULTA " + "="*20)
    print(f"  - Cita ID: {context.user_data.get('appointment_id')}")
    print(f"  - Tipo de Consulta: {context.user_data.get('consultation_type')}")
    print(f"  - Motivo de Visita: {context.user_data.get('reason_for_visit')}")
    print(f"  - ¿Es Primer Embarazo?: {context.user_data.get('is_first_pregnancy')}")
    print(f"  - ¿Ha Estado Embarazada?: {context.user_data.get('has_been_pregnant')}")
    print("="*70 + "\n")
    context.user_data['flow'] = preconsultation_flow
    start_node_id = preconsultation_flow['start_node']

    if query:
        try:
            # Borra el mensaje del menú principal para empezar en limpio
            await query.message.delete()
        except BadRequest:
            pass
    
    # Si no es query, borramos el /start del usuario si podemos
    elif update.message:
        try:
            await update.message.delete()
        except BadRequest:
            pass

    # Preparamos el texto del primer nodo
    first_node = preconsultation_flow['nodes'][start_node_id]
    intro_text = texts.get_text('preconsulta.start_intro')
    first_question_text = ""

    if 'section_header_key' in first_node:
        first_question_text += texts.get_text(first_node['section_header_key'], "") + "\n\n"

    first_question_text += texts.get_text(first_node['text_key'])
    full_initial_text = f"{intro_text}\n\n{first_question_text}"

    # Enviamos el primer mensaje, que se convertirá en nuestro "mensaje ancla"
    anchor_message = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=full_initial_text,
        parse_mode=ParseMode.HTML
    )

    # Guardamos los datos iniciales para el motor de flujos
    context.user_data['anchor_message_id'] = anchor_message.message_id
    context.user_data['current_node_id'] = start_node_id

    return AWAITING_GENERIC_INPUT