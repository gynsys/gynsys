# features/preconsulta/patient_flow/flow_actions/loop.py

from telegram.ext import ContextTypes
from ..gyn_history_handlers import get_ordinal
from ...flow_actions.handlers.obstetric_handlers import process_obstetric_history_from_table



async def prepare(update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Prepara e inicia un bucle si es necesario."""
    # Calculamos el número de iteraciones
    val1 = int(context.user_data.get('gyn_para', 0))
    val2 = int(context.user_data.get('gyn_cesarean', 0))
    total_iterations = val1 + val2

    if total_iterations > 0:
        # Preparamos las variables del bucle en user_data
        context.user_data['loop_variable'] = {
            "name": node['loop_variable'], # ej. "children_details"
            "total": total_iterations,
            "index": 0, # Empezamos en el índice 0
            "next_node_in_loop": node['next_node_in_loop'],
            "next_node_after_loop": node['next_node_after_loop']
        }
        # Creamos la lista vacía para los resultados
        context.user_data[node['loop_variable']] = []

        from ..generic_flow_engine import render_node
        return await render_node(update, context, node['next_node_in_loop'])
    else:
        # Si no hay iteraciones, saltamos directamente al final del bucle
        from ..generic_flow_engine import render_node
        return await render_node(update, context, node['next_node_after_loop'])

async def step(update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    """Ejecuta un paso del bucle: avanza al siguiente o termina."""
    loop_info = context.user_data.get('loop_variable')
    from ..generic_flow_engine import render_node

    print("\n" + "#"*20 + " [LOOP_STEP] INICIANDO " + "#"*20)
    print(f"--- [LOOP_STEP] Estado del bucle ANTES de avanzar: {loop_info}")

    # --- Lógica de Sub-Bucle (si la implementamos en el futuro) ---
    if 'sub_loop' in loop_info:
        sub_loop = loop_info['sub_loop']
        sub_loop['index'] += 1
        print(f"--- [LOOP_STEP] SUB-BUCLE. Nuevo índice: {sub_loop['index']} de {sub_loop['total']} ---")

        if sub_loop['index'] < sub_loop['total']:
            start_node = sub_loop['start_node']
            print(f"--- [LOOP_STEP] SUB-BUCLE continúa. Volviendo a '{start_node}' ---")
            print("#"*50 + "\n")
            return await render_node(update, context, start_node)
        else:
            print(f"--- [LOOP_STEP] SUB-BUCLE terminado. ---")
            del loop_info['sub_loop']

    # --- Lógica de Bucle Principal ---
    loop_info['index'] += 1
    print(f"--- [LOOP_STEP] BUCLE PRINCIPAL. Nuevo índice: {loop_info['index']} de {loop_info['total']} ---")

    if loop_info['index'] < loop_info['total']:
        next_node = loop_info['next_node_in_loop']
        print(f"--- [LOOP_STEP] BUCLE PRINCIPAL continúa. Yendo a '{next_node}' ---")
        print("#"*50 + "\n")
        return await render_node(update, context, next_node)
    else:
        next_node_id = loop_info['next_node_after_loop']
        print(f"--- [LOOP_STEP] BUCLE PRINCIPAL terminado. Yendo a '{next_node_id}' ---")
        print("#"*50 + "\n")
        context.user_data.pop('loop_variable', None)
        return await render_node(update, context, next_node_id)