"""
Handlers para flujo obstétrico: Embarazos, bucles de hijos, cálculo HO.
Interacción con Telegram y contexto del flujo.
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from common import texts
from ..services.formula_calculator import (
    calculate_ho_formula,
    calculate_ho_from_table,
    get_primigesta_formula,
    get_nuligesta_formula,
)

logger = logging.getLogger(__name__)


async def decide_obstetric_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """
    Decide si es necesario preguntar el historial obstétrico, cubriendo 4 casos clave.
    """
    user_data = context.user_data
    consultation_type = user_data.get('consultation_type')
    is_first_pregnancy = user_data.get('is_first_pregnancy')
    has_been_pregnant = user_data.get('has_been_pregnant')

    # Normalizar valores para evitar problemas con SQLite (0/1) o strings
    is_first = bool(is_first_pregnancy) if is_first_pregnancy is not None else None
    has_been = bool(has_been_pregnant) if has_been_pregnant is not None else None
    
    # Normalizar tipo de consulta (minúsculas y sin espacios)
    c_type = str(consultation_type or "").strip().lower()

    logger.info(
        f"Decidiendo flujo obstétrico: Tipo='{c_type}', "
        f"is_first={is_first}, has_been={has_been}"
    )

    # CASO ESPECIAL: Link Directo (Forzamos la pregunta manual)
    if user_data.get('is_direct_link'):
        logger.info("Caso Link Directo: Forzando pregunta de embarazo manual.")
        return 'ASK_PREGNANCY_BOOL_NEW'

    # CASO 1: Prenatal + Sin embarazos previos -> PRIMIGESTA
    if 'prenatal' in c_type and is_first is True:
        logger.info("Caso 1: Prenatal-Primigesta. Saltando bucle HO.")
        user_data['gyn_ho'] = get_primigesta_formula()
        return node['next_if_skip']

    # CASO 2: Prenatal + Con embarazos previos -> NECESITA HO
    if 'prenatal' in c_type and is_first is False:
        logger.info("Caso 2: Prenatal-Multigesta. Entrando a bucle HO.")
        return node['next_if_needed']

    # CASO 3: Ginecológica/Ginecología + Sin embarazos previos -> NULIGESTA
    if ('ginec' in c_type) and has_been is False:
        logger.info("Caso 3: Ginecológica-Nuligesta. Saltando bucle HO.")
        user_data['gyn_ho'] = get_nuligesta_formula()
        return node['next_if_skip']

    # CASO 4: Ginecológica/Ginecología + Con embarazos previos -> NECESITA HO
    if ('ginec' in c_type) and has_been is True:
        logger.info("Caso 4: Ginecológica con historial. Entrando a bucle HO.")
        return node['next_if_needed']

    # Fallback: Por seguridad, si no sabemos nada, preguntamos
    logger.warning("Caso Fallback: No se pudo determinar el flujo obstétrico. Redirigiendo a pregunta manual.")
    return 'ASK_PREGNANCY_BOOL_NEW'


async def prepare_obstetric_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Decide qué rama del historial obstétrico seguir basado en el tipo de consulta."""
    from ...patient_flow.generic_flow_engine import render_node

    consultation_type = context.user_data.get('consultation_type', 'Ginecológica')

    if consultation_type == 'Prenatal':
        context.user_data['is_prenatal_flow'] = True
        return await render_node(update, context, node['next_if_prenatal'])
    else:
        return await render_node(update, context, node['next_if_gyn'])


async def prepare_prenatal_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Marca el flujo como prenatal para el cálculo posterior del HO."""
    context.user_data['is_prenatal_flow'] = True
    return node.get('next_node')


async def prepare_single_prenatal_record(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Prepara la estructura de datos para un único embarazo actual."""
    context.user_data['obstetric_history'] = [{
        'type': 'Embarazo actual',
        'is_first_pregnancy': True
    }]
    context.user_data['HO_formula'] = "G1 P0 A0 C0"
    return node.get('next_node')


async def finalize_single_prenatal_record(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Toma las semanas del embarazo actual y las guarda en la estructura de datos correcta."""
    weeks = context.user_data.get('current_pregnancy_weeks', 'N/A')

    if 'obstetric_history' in context.user_data and context.user_data['obstetric_history']:
        context.user_data['obstetric_history'][0]['gestational_weeks'] = weeks

    context.user_data.pop('current_pregnancy_weeks', None)
    return node.get('next_node')


async def calculate_ho_action(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Calcula la fórmula HO a partir de los datos recopilados."""
    logger.info("Ejecutando acción para calcular HO...")
    user_data = context.user_data

    ho_summary = calculate_ho_formula(user_data)
    user_data['gyn_ho'] = ho_summary

    print(f"DEBUG - Historial Obstétrico Calculado: {ho_summary}")
    return node.get('next_node')


async def process_obstetric_history_from_table(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Calcula la fórmula HO a partir de los datos de la tabla."""
    logger.info("Calculando HO desde datos disponibles...")
    user_data = context.user_data

    ho_summary = calculate_ho_from_table(user_data)
    user_data['gyn_ho'] = ho_summary

    print(f"DEBUG - Historial Obstétrico Calculado: {ho_summary}")
    return node.get('next_node')


async def prepare_birth_details_loop(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Lee los resultados de la tabla HO y prepara un bucle para los detalles de cada bebé nacido."""
    from ...patient_flow.generic_flow_engine import render_node

    ho_results = context.user_data.get('ho_table_results', {})
    sencillos = ho_results.get('single_pregnancies', 0)
    multiples = ho_results.get('multiple_pregnancies', 0)

    total_babies = sencillos + (multiples * 2)

    if total_babies > 0:
        # Mensaje de transición
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=context.user_data['anchor_message_id'],
            text=texts.get_text("preconsulta.children_details_intro"),
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(1.5)

        context.user_data['loop_variable'] = {
            "name": "birth_details",
            "total": total_babies,
            "index": 0,
            "next_node_in_loop": node['next_node_in_loop'],
            "next_node_after_loop": node['next_node_after_loop']
        }
        context.user_data["birth_details"] = [{} for _ in range(total_babies)]
        return await render_node(update, context, node['next_node_in_loop'])
    else:
        return await render_node(update, context, node['next_node_after_loop'])


async def prepare_pregnancy_type_loop(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Prepara el bucle para tipos de embarazo."""
    from ...patient_flow.generic_flow_engine import render_node
    total = int(context.user_data.get(node['loop_counter'], 0))
    if total > 0:
        context.user_data['loop_variable'] = {
            "name": node['loop_variable'],
            "total": total,
            "index": 0,
            "next_node_in_loop": node['next_node_in_loop'],
            "next_node_after_loop": node['next_node_after_loop']
        }
        context.user_data[node['loop_variable']] = [{} for _ in range(total)]
        return await render_node(update, context, node['next_node_in_loop'])
    else:
        context.user_data['obstetric_history_summary'] = "Nuligesta"
        return await render_node(update, context, node['next_node_after_loop'])


async def prepare_children_loops(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Prepara los bucles para procesar hijos de embarazos múltiples y sencillos."""
    from ...patient_flow.generic_flow_engine import render_node
    if not context.user_data.get('processed_multiples', False):
        context.user_data['processed_multiples'] = True
        children_to_process = [
            (i, p.get('multiple_type', 'Gemelos/Mellizos'))
            for i, p in enumerate(context.user_data.get('pregnancies', []))
            if p.get('type') == 'Múltiple'
        ]
        if children_to_process:
            context.user_data['children_loop'] = {
                "queue": children_to_process,
                "child_index": 0,
                "parent_pregnancy_index": -1
            }
            return await render_node(update, context, "START_MULTIPLE_CHILDREN_LOOP")
    if not context.user_data.get('processed_singles', False):
        context.user_data['processed_singles'] = True
        children_to_process = [
            (i, 'Sencillo')
            for i, p in enumerate(context.user_data.get('pregnancies', []))
            if p.get('type') == 'Sencillo'
        ]
        if children_to_process:
            context.user_data['children_loop'] = {
                "queue": children_to_process,
                "child_index": 0,
                "parent_pregnancy_index": -1
            }
            return await render_node(update, context, "START_SINGLE_CHILDREN_LOOP")
    return await render_node(update, context, node['next_node'])


async def ask_child_data_step(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Procesa un paso en el bucle de datos de hijos."""
    from ...patient_flow.generic_flow_engine import render_node
    if 'children_loop' not in context.user_data:
        return await render_node(update, context, node['next_node_after_loop'])
    child_loop = context.user_data['children_loop']
    if child_loop['parent_pregnancy_index'] != child_loop['queue'][0][0]:
        child_loop['parent_pregnancy_index'] = child_loop['queue'][0][0]
        child_loop['child_index'] = 0
    parent_pregnancy = context.user_data['pregnancies'][child_loop['parent_pregnancy_index']]
    multiple_type = parent_pregnancy.get('multiple_type', 'Sencillo').lower()
    total_children_in_pregnancy = 2 if 'gemelos' in multiple_type else 3 if 'trillizos' in multiple_type else 1
    if child_loop['child_index'] < total_children_in_pregnancy:
        context.user_data['child_header_text'] = (
            f"👶 Datos del bebé {child_loop['child_index'] + 1} de {total_children_in_pregnancy} "
            f"(Embarazo {child_loop['parent_pregnancy_index'] + 1})"
        )
        child_loop['child_index'] += 1
        return await render_node(update, context, "ASK_CHILD_BIRTH_YEAR")
    else:
        child_loop['queue'].pop(0)
        if not child_loop['queue']:
            del context.user_data['children_loop']
            return await render_node(update, context, node['next_node_after_loop'])
        else:
            return await ask_child_data_step(update, context, node)


async def prepare_children_sub_loop(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Prepara un sub-bucle para hijos de embarazos múltiples."""
    loop_info = context.user_data.get('loop_variable')
    if not loop_info:
        return node.get('next_node')
    current_pregnancy = context.user_data[loop_info['name']][loop_info['index']]
    multiple_type = current_pregnancy.get('multiple_type', '').lower()
    count = (
        2 if 'gemelos' in multiple_type else
        3 if 'trillizos' in multiple_type else
        int(current_pregnancy.get('multiple_count', 4)) if 'cuatrillizos' in multiple_type else 1
    )
    if count > 1:
        loop_info['sub_loop'] = {"index": 0, "total": count, "start_node": "ASK_BIRTH_WEIGHT"}
    current_pregnancy['children'] = [{} for _ in range(count)]
    return node.get('next_node')


async def prepare_children_details_loop(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Prepara el bucle para detalles de hijos."""
    from ...patient_flow.generic_flow_engine import render_node

    ho_results = context.user_data.get('ho_table_results', {})
    partos_sencillos = ho_results.get('parto_sencillo', 0)
    partos_multiples = ho_results.get('parto_multiple', 0)

    total_babies = partos_sencillos + (partos_multiples * 2)

    if total_babies > 0:
        context.user_data['loop_variable'] = {
            "name": "children_details",
            "total": total_babies,
            "index": 0,
            "next_node_in_loop": node['next_node_in_loop'],
            "next_node_after_loop": node['next_node_after_loop']
        }
        context.user_data["children_details"] = [{} for _ in range(total_babies)]
        return await render_node(update, context, node['next_node_in_loop'])
    else:
        return await render_node(update, context, node['next_node_after_loop'])


async def start_children_details_loop(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Inicia el bucle de detalles de hijos."""
    from ...patient_flow.generic_flow_engine import render_node
    loop_info = context.user_data.get('loop_variable', {})
    if loop_info and loop_info.get('total', 0) > 0:
        return await render_node(update, context, loop_info['next_node_in_loop'])
    else:
        return await render_node(update, context, loop_info.get('next_node_after_loop'))

