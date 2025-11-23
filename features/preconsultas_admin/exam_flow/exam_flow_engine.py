import json
import logging
from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes
from telegram.error import BadRequest

# Importamos las acciones específicas de este flujo
from . import exam_actions
# Importamos los renderizadores y procesadores genéricos que ya tienes

from . import exam_text_input, exam_yes_no, exam_checklist, exam_buttons
logger = logging.getLogger(__name__)

from ..states import AWAITING_EXAM_INPUT

def log_exam_flow(step, **kwargs):
    details = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"[EXAM_FLOW] | {step} | {details}")
# Cargamos la definición del flujo del examen
try:
    with open('features/preconsultas_admin/flows/physical_exam_flow.json', 'r', encoding='utf-8') as f:
        physical_exam_flow = json.load(f)
except FileNotFoundError:
    logger.error("¡CRÍTICO! No se encontró el archivo 'physical_exam_flow.json'")
    physical_exam_flow = None

# Mapeo de tipos de nodo a sus manejadores
RENDERERS = {
    'buttons': exam_buttons.render,
    'numeric_input': exam_text_input.render,
    'text_input': exam_text_input.render,
    'checklist': exam_checklist.render,
    'yes_no': exam_yes_no.render,
}
PROCESSORS = {
    'buttons': exam_buttons.process,
    'numeric_input': exam_text_input.process,
    'text_input': exam_text_input.process,
    'checklist': exam_checklist.process,
    'yes_no': exam_yes_no.process,
}
ACTION_HANDLERS = {
    'calculate_imc': exam_actions.calculate_imc,
    'decide_secrecion_subflujo': exam_actions.decide_secrecion_subflujo,
    'combine_examen_fisico_summary': exam_actions.combine_examen_fisico_summary,
}



async def start_exam_flow(update, context):
    log_exam_flow("START", node_id=physical_exam_flow['start_node'])
    if physical_exam_flow is None:
        if update.callback_query: await update.callback_query.answer("❌ Error: Flujo no disponible.", show_alert=True)
        return ConversationHandler.END

    context.user_data['flow'] = physical_exam_flow
    start_node_id = physical_exam_flow['start_node']
    return await render_exam_node(update, context, start_node_id)


async def render_exam_node(update, context, node_id):
    log_exam_flow("RENDER_NODE", node_id=node_id)
    node = context.user_data['flow']['nodes'][node_id]
    context.user_data['current_node_id'] = node_id
    node_type = node.get('type')
    log_exam_flow("RENDER_NODE", node_type=node_type)

    if node_type == 'action':
        handler_name = node.get('handler')
        handler = ACTION_HANDLERS.get(handler_name)
        log_exam_flow("ACTION", handler=handler_name)
        if handler:
            next_node_id_or_signal = await handler(update, context, node)
            log_exam_flow("ACTION_RESULT", result=next_node_id_or_signal)
            if next_node_id_or_signal == "END_SUBFLOW":
                return "END_SUBFLOW"
            if next_node_id_or_signal:
                return await render_exam_node(update, context, next_node_id_or_signal)
        return AWAITING_EXAM_INPUT

    renderer = RENDERERS.get(node_type)
    if renderer:
        log_exam_flow("RENDER", renderer=renderer.__name__)
        await renderer(update, context, node) # Quitamos el message_id de aquí, debe estar en el render
        return AWAITING_EXAM_INPUT

    logger.error(f"Renderizador no encontrado para el tipo de nodo: {node_type}")
    return ConversationHandler.END


async def process_exam_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_exam_flow("PROCESS_INPUT", update_type="Query" if update.callback_query else "Message")
    current_node_id = context.user_data.get('current_node_id')
    if not current_node_id:
        log_exam_flow("PROCESS_ERROR", reason="No current_node_id")
        return ConversationHandler.END

    node = context.user_data['flow']['nodes'][current_node_id]
    node_type = node.get('type')
    log_exam_flow("PROCESS_INPUT", current_node=current_node_id, node_type=node_type)

    next_node_id = None
    processor = None

    if update.callback_query and node_type in PROCESSORS:
        processor = PROCESSORS.get(node_type)
    elif update.message and node_type in ['numeric_input', 'text_input']:
        processor = PROCESSORS.get(node_type)
    elif update.message:
        log_exam_flow("PROCESS_IGNORE", reason="Texto recibido en un nodo que no es de input")
        try: await update.message.delete()
        except BadRequest: pass
        return AWAITING_EXAM_INPUT

    if processor:
        log_exam_flow("PROCESS", processor=processor.__name__)
        next_node_id = await processor(update, context, node)
        log_exam_flow("PROCESS_RESULT", next_node=next_node_id)

    if next_node_id:
        final_state_or_signal = await render_exam_node(update, context, next_node_id)
        log_exam_flow("TRANSITION", result=final_state_or_signal)
        if final_state_or_signal == "END_SUBFLOW":

            from ..admin_handlers import transition_to_ultrasound
            return await transition_to_ultrasound(update, context)
        return final_state_or_signal
    return AWAITING_EXAM_INPUT