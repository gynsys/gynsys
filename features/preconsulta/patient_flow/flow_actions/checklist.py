# features/preconsulta/patient_flow/flow_actions/checklist.py

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest
from features.preconsulta.components import keyboards
from common import texts
from features.preconsulta.states import AWAITING_GENERIC_INPUT
from . import loop


logger = logging.getLogger(__name__)

async def process_other_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    other_text = update.message.text
    await update.message.delete()

    return_node_id = context.user_data.pop('checklist_return_node', None)
    if not return_node_id:
        return ConversationHandler.END

    node = context.user_data['flow']['nodes'][return_node_id]
    save_key = f"{node['save_to']}_selected"
    selected_items = context.user_data.setdefault(save_key, set())

    selected_items.add(f"Otro: {other_text.strip()}")

    from ..generic_flow_engine import render_node

    # Llamamos a render_node para que MUESTRE el checklist de nuevo
    await render_node(update, context, return_node_id)

    # Devolvemos el estado correcto para que la conversación continúe esperando
    from ...states import AWAITING_GENERIC_INPUT
    return AWAITING_GENERIC_INPUT

async def render(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict, message_id: int = None):
    """Muestra un teclado de checklist editando el mensaje ancla."""
    text_content = ""
    if 'section_header_key' in node:
        text_content += texts.get_text(node['section_header_key'], "") + "\n\n"

    text_content += texts.get_text(node['text_key'], "Selecciona las opciones:")

    save_key = f"{node['save_to']}_selected"
    selected_items = context.user_data.get(save_key, set())

    node_id = context.user_data['current_node_id']
    keyboard_type = node.get('keyboard_type')

    keyboard_generators = {
        'pathologies': keyboards.get_pathologies_keyboard,
        'mac': keyboards.get_mac_keyboard,
        'complications': keyboards.get_complications_keyboard,
        'leg_pain_type': keyboards.get_leg_pain_type_keyboard,
        'leg_pain_zone': keyboards.get_leg_pain_zone_keyboard,
        'gastro_symptoms': keyboards.get_gastro_symptoms_keyboard,
        'substances': keyboards.get_substances_keyboard
    }

    reply_markup = None
    if keyboard_type in keyboard_generators:
        reply_markup = keyboard_generators[keyboard_type](node_id, selected=selected_items)
    else:
        logger.error(f"Tipo de teclado de checklist desconocido: '{keyboard_type}'")
        # Puedes añadir un mensaje de error al usuario aquí si quieres
    
    target_message_id = message_id or context.user_data.get('anchor_message_id') or context.user_data.get('consultation_anchor_message_id')
    
    # --- LÓGICA CORREGIDA: Intentar editar, si falla enviar nuevo mensaje ---
    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=target_message_id,
            text=text_content,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    except BadRequest as e:
        # Si el mensaje no existe, enviar uno nuevo
        if "message to edit not found" in str(e).lower() or "message can't be edited" in str(e).lower():
            new_message = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text_content,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            # Actualizar el anchor_message_id
            context.user_data['anchor_message_id'] = new_message.message_id
        else:
            raise
    # --- FIN DE LA CORRECCIÓN ---

    return AWAITING_GENERIC_INPUT
async def process(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    query = update.callback_query
    await query.answer()
    node_id = context.user_data['current_node_id']
    selection = query.data.replace(f"{node_id}_", "")

    save_key = f"{node['save_to']}_selected"
    selected_items = context.user_data.setdefault(save_key, set())

    # --- INICIO DE LA LÓGICA CORREGIDA ---

    # CASO 1: El usuario ha terminado la selección.
    if selection == 'done':
        final_text = "Sí, no especificado"

        if selected_items:
            final_text_parts = []
            other_texts = []

            options_maps = {
                'pathologies': {"diabetes": "Diabetes", "tiroides": "Tiroides", "asma": "Asma", "alergias": "Alergias", "inmunologicas": "Enfermedades Inmunológicas", "cardiovasculares": "Enfermedades Cardiovasculares", "respiratorias": "Enfermedades Respiratorias", "renales": "Enfermedades Renales", "intestino_irritable": "Síndrome de Intestino Irritable"},
                'mac': {"pastillas": "Pastillas", "diu": "DIU", "inyeccion": "Inyección", "implante": "Implante", "anillo": "Anillo Vaginal", "parche": "Parche", "condones": "Condones", "ritmo": "Método del Ritmo", "coitus_interruptus": "Coitus Interruptus"},
                'birth_complications': {"preeclampsia": "Preclamsia", "placenta_previa": "Placenta Previa", "hemorragia": "Hemorragias", "none": "Sin complicaciones"},
                'leg_pain_type': {"punzante": "Punzante", "quemante": "Quemante", "corriente": "Corriente", "hormigueo": "Hormigueo"},
                'leg_pain_zone': {"lateral": "Lateral", "interna": "Interna", "posterior": "Posterior", "gluteos": "Zona de glúteos"},
                'gastro_symptoms': {"nauseas": "Nauseas", "vomitos": "Vómitos", "inflamacion": "Inflamación", "distension": "Distensión abdominal", "dolor_evacuar": "Dolor al evacuar", "colicos": "Cólicos", "flatulencias": "Flatulencias"},
                'substances': {"alcohol": "Alcohol","cannabis": "Marihuana/cannabis", "cocaine": "Cocaína", "amphetamines": "Anfetaminas", "opioids": "Opioides", "benzos": "Benzodiacepinas", "hallucinogens": "Alucinógenos","other": "Otras sustancias"}
            }

            current_map = options_maps.get(node.get('keyboard_type'), {})
            for item in sorted(list(selected_items)):
                if item.startswith("Otro:"):
                    other_texts.append(item.replace("Otro: ", ""))
                else:
                    final_text_parts.append(current_map.get(item, item))

            final_text = ", ".join(final_text_parts)
            if other_texts:
                final_text += (", " if final_text else "") + "Otro: " + ", ".join(other_texts)

        context.user_data[node['save_to']] = final_text
        context.user_data.pop(save_key, None)
        return node.get('next_node')

    # CASO 2: El usuario quiere escribir una opción "Otro".
    elif selection == 'other':
        context.user_data['checklist_return_node'] = context.user_data['current_node_id']
        other_prompt_key = node.get('other_prompt_key', 'preconsulta.other_prompt_personal')
        await query.edit_message_text(text=texts.get_text(other_prompt_key))
        from ...states import AWAITING_CHECKLIST_OTHER
        return AWAITING_CHECKLIST_OTHER

    # CASO 3: Es una selección normal de un ítem de la lista.
    else:
        if selection == 'none':
            if 'none' in selected_items:
                selected_items.clear()
            else:
                selected_items.clear()
                selected_items.add('none')
        else:
            selected_items.discard('none')
            if selection in selected_items:
                selected_items.remove(selection)
            else:
                selected_items.add(selection)

    # --- Bloque de refresco del teclado ---
    keyboard_type = node.get('keyboard_type')
    keyboard_generators = {
        'pathologies': keyboards.get_pathologies_keyboard,
        'mac': keyboards.get_mac_keyboard,
        'birth_complications': keyboards.get_birth_complications_keyboard,
        'leg_pain_type': keyboards.get_leg_pain_type_keyboard,
        'leg_pain_zone': keyboards.get_leg_pain_zone_keyboard,
        'gastro_symptoms': keyboards.get_gastro_symptoms_keyboard
        # Nota: el teclado de 'substances' es manejado por 'special_checklist.py'
    }

    if keyboard_type in keyboard_generators:
        new_keyboard = keyboard_generators[keyboard_type](node_id, selected=selected_items)
        try:
            await query.edit_message_reply_markup(reply_markup=new_keyboard)
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                logger.warning(f"Error al refrescar checklist: {e}")

    # Después de procesar un clic (que no sea 'done' u 'other'), nos quedamos en el mismo paso.
    return None