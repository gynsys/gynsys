import logging
from .exam_summary_builder import build_summary_text
logger = logging.getLogger(__name__)

# En features/preconsultas_admin/exam_flow/exam_actions.py

async def calculate_imc(update, context, node):
    try:
        # 1. Obtenemos los valores como texto
        peso_str = context.user_data.get('peso_kg', '0')
        altura_str = context.user_data.get('altura_cm', '0')

        # 2. Normalizamos la entrada: reemplazamos comas por puntos
        peso_normalizado = peso_str.replace(',', '.')
        altura_normalizada = altura_str.replace(',', '.')

        # 3. Intentamos convertir los valores normalizados
        peso = float(peso_normalizado)
        altura_cm = float(altura_normalizada)

        if peso > 0 and altura_cm > 0:
            # El cálculo se realiza con los valores ya convertidos
            imc = round(peso / (altura_cm ** 2), 2)
            context.user_data['imc_calculado'] = imc
        else:
            # Si los números son 0 o negativos, no calculamos
            context.user_data['imc_calculado'] = "N/A"

    except (ValueError, TypeError):
        # Si la conversión a float falla incluso después de normalizar, marcamos como N/A
        context.user_data['imc_calculado'] = "N/A"

    return node.get('next_node')



async def decide_secrecion_subflujo(update, context, node):
    """
    Decide si es necesario entrar en los sub-flujos para detallar la secreción
    blanca o con sangrado.
    """
    # Usamos .get(..., set()) para evitar errores si la clave no existe
    selected_types = context.user_data.get('secrecion_vaginal_tipo_selected', set())

    # Comprobación para secreción blanca
    if 'Blanca' in selected_types and 'secrecion_blanca_detalle' not in context.user_data:
        return node.get('next_if_blanca')

    # Comprobación para sangrado
    if 'Con Sangrado' in selected_types and 'secrecion_sangre_detalle' not in context.user_data:
        return node.get('next_if_sangrado')

    # Si no se cumple ninguna de las condiciones anteriores, se continúa al siguiente paso
    return node.get('next_if_done')



async def combine_examen_fisico_summary(update, context, node):
    """
    Llama al constructor de resúmenes y guarda el resultado final.
    """
    # 1. Llama a la función dedicada para construir el texto.
    summary_text = build_summary_text(context.user_data)

    # 2. Guarda el resumen final en la clave que el sistema principal espera.
    context.user_data['admin_physical_exam'] = summary_text

    logger.info(f"Resumen de Examen Físico generado: {summary_text}")

    # 3. Devuelve la señal para terminar el sub-flujo.
    return node.get('next_node')