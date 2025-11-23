import json
import logging
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

def to_roman(num):
    if not isinstance(num, int) or not 0 < num < 4000:
        return str(num)
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syb = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num

def _format_date_for_summary(date_str):
    if not date_str or date_str.lower() in ['nunca', 'no', 'n/a']:
        return None
    try:
        months_es = {
            '01': 'enero', '02': 'febrero', '03': 'marzo', '04': 'abril',
            '05': 'mayo', '06': 'junio', '07': 'julio', '08': 'agosto',
            '09': 'septiembre', '10': 'octubre', '11': 'noviembre', '12': 'diciembre'
        }
        if len(date_str) >= 7:
            year, month_num = date_str[:4], date_str[5:7]
            month_name = months_es.get(month_num, '')
            if month_name:
                return f"{month_name} del {year}"
        return date_str
    except Exception:
        return date_str

def _build_gyn_summary(user_data: dict) -> str:
    summary_parts = []
    ho_formula = user_data.get('gyn_ho', '')
    g_match, p_match, a_match, c_match = re.search(r"G(\d+)", ho_formula), re.search(r"P(\d+)", ho_formula), re.search(r"A(\d+)", ho_formula), re.search(r"C(\d+)", ho_formula)
    g, p, a, c = (int(m.group(1)) if m else 0 for m in [g_match, p_match, a_match, c_match])

    if 'nuligesta' in ho_formula.lower() or 'primigesta' in ho_formula.lower():
        summary_parts.append("Paciente primigesta." if 'primigesta' in ho_formula.lower() else "Paciente nuligesta.")
    elif g > 0:
        ho_parts = []
        if g > 0: ho_parts.append(f"{to_roman(g)}G")
        if p > 0: ho_parts.append(f"{to_roman(p)}P")
        if a > 0: ho_parts.append(f"{to_roman(a)}A")
        if c > 0: ho_parts.append(f"{to_roman(c)}C")
        ho_roman_text = " ".join(ho_parts)
        
        # --- CORRECCIÓN #1: Manejo robusto de datos (lista o string JSON) ---
        birth_details_data = user_data.get('birth_details')
        birth_list = []
        if isinstance(birth_details_data, str):
            try:
                birth_list = json.loads(birth_details_data)
            except (json.JSONDecodeError, TypeError): pass
        elif isinstance(birth_details_data, list):
            birth_list = birth_details_data
        
        birth_summary_line = ""
        if birth_list:
            birth_summary_parts = []
            for birth in birth_list:
                year, weight, height = birth.get('birth_year', 'N/A'), birth.get('weight', 'N/A'), birth.get('height', 'N/A')
                complications = birth.get('complications', 'Sin complicaciones')
                prefix_complicaciones = "con " if "Sin complicaciones" not in complications else ""
                birth_text = f"{year} {weight} kg / {height} cm, que cursó {prefix_complicaciones}{complications}"
                birth_summary_parts.append(birth_text)
            birth_summary_line = " -> " + "; ".join(birth_summary_parts)
            
        full_ho_details = f"{ho_roman_text}{birth_summary_line}"
        if full_ho_details.strip():
            summary_parts.append(f"Paciente con {full_ho_details.strip()}.")

    menarche, sexarche = user_data.get('gyn_menarche'), user_data.get('gyn_sexarche')
    menarquia_text = f"Menarquía a los {menarche} años" if menarche else ""
    sexarquia_text = "Sexarquía: niega" if sexarche and 'nunca' in str(sexarche).lower() else f"sexarquía a los {sexarche}" if sexarche else ""
    if menarquia_text and sexarquia_text:
        summary_parts.append(f"{menarquia_text} y {sexarquia_text}.")
    elif menarquia_text:
        summary_parts.append(f"{menarquia_text}.")
    elif sexarquia_text:
        summary_parts.append(f"{sexarquia_text.capitalize()}.")

    cycles, dismenorrhea = user_data.get('gyn_cycles', 'Regulares'), user_data.get('gyn_dysmenorrhea', 'No')
    cycle_text = "ciclos menstruales regulares"
    if cycles and 'irregulares' in cycles.lower():
        match = re.search(r"Duración: ([\w\s]+)\. Frecuencia: ([\w\s]+)\.", cycles)
        if match:
            duration, frequency = match.groups()
            cycle_text = f"ciclos menstruales irregulares con duración de {duration.strip()} y frecuencia de {frequency.strip()}"
    if dismenorrhea.lower() != 'no':
        match = re.search(r"intensidad: (\d+)/10", dismenorrhea)
        intensity = match.group(1) if match else "N/A"
        cycle_text += f", asociados a dismenorrea de intensidad {intensity}/10."
    else:
        cycle_text += ", sin dismenorrea."
    summary_parts.append(f"Refiere {cycle_text}")

    fum, mac = user_data.get('gyn_fum'), user_data.get('gyn_mac')
    if fum: summary_parts.append(f"Su FUM fue el {fum}.")
    if mac and mac.lower() != 'no':
        summary_parts.append(f"Utiliza como método anticonceptivo: {mac.lower()}.")
    
    sexually_active, fertility_intent = user_data.get('sexually_active'), user_data.get('gyn_fertility_intent')
    if sexually_active and sexually_active.lower() == 'sí':
        fertility_text = "sin deseo de fertilidad"
        if fertility_intent and 'no tiene' not in fertility_intent.lower():
             fertility_text = f"con {fertility_intent.lower()}"
        summary_parts.append(f"Mantiene actividad sexual activa {fertility_text}.")
    else:
        summary_parts.append("No mantiene actividad sexual actualmente.")

    prev_checkup, last_pap = user_data.get('gyn_previous_checkups'), user_data.get('gyn_last_pap_smear')
    prev_checkup_formatted = _format_date_for_summary(prev_checkup)
    last_pap_formatted = _format_date_for_summary(last_pap)
    
    # --- CORRECCIÓN #2: Eliminado "el" de la frase fija ---
    if prev_checkup and last_pap and prev_checkup == last_pap and prev_checkup.lower() != 'nunca':
        summary_parts.append(f"Su último control ginecológico y citología fueron en {prev_checkup_formatted}.")
    else:
        if prev_checkup and prev_checkup.lower() != 'nunca':
            summary_parts.append(f"Su último control ginecológico fue en {prev_checkup_formatted}.")
        if last_pap and last_pap.lower() != 'nunca':
            summary_parts.append(f"Su última citología fue realizada en {last_pap_formatted}.")
            
    return " ".join(part for part in summary_parts if part)

def _build_functional_exam_summary(user_data: dict) -> str:
    """
    Construye el resumen del examen funcional.
    Si no hay datos de examen funcional (porque fue deshabilitado), retorna None para que no se incluya en el PDF.
    """
    # Verificar si hay algún dato de examen funcional
    has_functional_data = any(
        user_data.get(key) for key in [
            'functional_dispareunia', 'functional_leg_pain', 'functional_gastro_before',
            'functional_gastro_during', 'functional_dischezia', 'functional_bowel_freq',
            'functional_urinary_problem', 'functional_urinary_pain', 'functional_urinary_irritation',
            'functional_urinary_incontinence', 'functional_urinary_nocturia'
        ]
    )
    
    # Si no hay datos, significa que el examen funcional fue deshabilitado
    # Retornar None para que no se incluya en el PDF
    if not has_functional_data:
        return None
    summary_parts = []
    dispareunia = user_data.get('functional_dispareunia', 'No')
    if dispareunia and 'sí' in dispareunia.lower():
        match = re.search(r"tipo (\w+) \(Intensidad: (\d+)/10\)", dispareunia)
        if match:
            tipo, intensidad_str = match.groups()
            intensidad = int(intensidad_str)
            desc_intensidad = "de alta intensidad" if intensidad >= 7 else "de moderada intensidad" if intensidad >= 4 else "de leve intensidad"
            summary_parts.append(f"La paciente refiere dispareunia de tipo {tipo.lower()} {desc_intensidad} ({intensidad}/10).")
        else:
            summary_parts.append("Refiere dispareunia.")
    else:
        summary_parts.append("Niega dispareunia.")
    leg_pain = user_data.get('functional_leg_pain', 'No')
    if leg_pain and 'sí' in leg_pain.lower():
        match = re.search(r"Tipo: ([\w\s,]+), Zona: ([\w\s,]+)", leg_pain)
        if match:
            tipo, zona = match.groups()
            summary_parts.append(f"Presenta dolor en miembros inferiores, descrito como '{tipo.lower()}' en la {zona.lower()}.")
        else:
            summary_parts.append("Refiere dolor en miembros inferiores no especificado.")
    else:
        summary_parts.append("Niega dolor en miembros inferiores durante la menstruación.")
    gastro_before, gastro_during, dischezia, bowel_freq = user_data.get('functional_gastro_before', 'No'), user_data.get('functional_gastro_during', 'No'), user_data.get('functional_dischezia', 'No'), user_data.get('functional_bowel_freq', 'N/A')
    symptoms_set = set()
    if gastro_before and gastro_before.lower() != 'no':
        symptoms_set.update(s.strip() for s in gastro_before.lower().split(','))
    if gastro_during and gastro_during.lower() != 'no':
        symptoms_set.update(s.strip() for s in gastro_during.lower().split(','))
    if symptoms_set or (dischezia and dischezia.lower() != 'no'):
        gastro_summary = "A nivel gastrointestinal, manifiesta"
        if "dolor al evacuar" in symptoms_set:
            symptoms_set.remove("dolor al evacuar")
        symptoms_text = ", ".join(sorted(list(symptoms_set)))
        final_symptoms = (symptoms_text + ", " if symptoms_text else "") + f"dolor al evacuar (disquecia {dischezia.lower()})" if dischezia.lower() != 'no' else symptoms_text
        if final_symptoms:
            gastro_summary += f" síntomas como {final_symptoms}."
        # Usar "de" solo si hay otros síntomas además de disquecia, o si disquecia no es "eventual"
        # Si solo hay disquecia eventual sin otros síntomas, no usar "de"
        has_other_symptoms = len(symptoms_set) > 0
        is_eventual_only = not has_other_symptoms and dischezia and 'eventual' in dischezia.lower()
        
        if is_eventual_only:
            # Solo disquecia eventual, sin otros síntomas: no usar "de"
            gastro_summary += f" Su frecuencia evacuatoria {bowel_freq.lower()}."
        else:
            # Hay otros síntomas o disquecia no eventual: usar "de"
            gastro_summary += f" Su frecuencia evacuatoria es de {bowel_freq.lower()}."
        summary_parts.append(gastro_summary)
    else:
        # Cuando no hay síntomas, no usar "de" antes de la frecuencia
        summary_parts.append(f"A nivel gastrointestinal, no refiere síntomas significativos, con una frecuencia evacuatoria {bowel_freq.lower()}.")
    urinary_problem = user_data.get('functional_urinary_problem', 'No')
    if urinary_problem and urinary_problem.lower() != 'no':
        urinary_parts = []
        urinary_pain = user_data.get('functional_urinary_pain', 'No')
        if urinary_pain and 'sí' in urinary_pain.lower():
            match = re.search(r"\(Intensidad: (\d+)/10\)", urinary_pain)
            if match:
                intensidad = int(match.group(1))
                desc_intensidad = "muy alta" if intensidad >= 7 else "moderada" if intensidad >= 4 else "leve"
                urinary_parts.append(f"dolor al orinar de intensidad {desc_intensidad} ({intensidad}/10)")
        other_urinary_symptoms = [s for s, k in [("irritación", 'functional_urinary_irritation'), ("incontinencia", 'functional_urinary_incontinence'), ("nocturia", 'functional_urinary_nocturia')] if user_data.get(k, 'No').lower() == 'sí']
        urinary_summary = "En el sistema urinario, confirma problemas"
        if urinary_parts:
            urinary_summary += f", con {urinary_parts[0]}"
            if other_urinary_symptoms:
                urinary_summary += ", acompañado de " + " y ".join(other_urinary_symptoms)
            urinary_summary += "."
        elif other_urinary_symptoms:
            urinary_summary += ", manifestando " + " y ".join(other_urinary_symptoms) + "."
        else:
            urinary_summary += " no especificados."
        summary_parts.append(urinary_summary)
    else:
        summary_parts.append("Hábito miccional conservado.")
    return " ".join(summary_parts)

def _build_habits_summary(user_data: dict) -> str:
    summary_parts = []
    activity_data = user_data.get('habits_physical_activity', 'No')
    if activity_data and 'sí' in activity_data.lower():
        freq_match = re.search(r"Frecuencia: ([\w\s/]+)[,.]", activity_data)
        dura_match = re.search(r"Duración: ([\w\s>]+ min)[,.]", activity_data)
        habit_match = re.search(r"Hábito: ([\w\sñ-]+)[,.]", activity_data)
        goal_match = re.search(r"Objetivo: (.+)", activity_data)
        frecuencia = freq_match.group(1).strip() if freq_match else ""
        duracion = dura_match.group(1).strip().replace(" min", "") if dura_match else ""
        habito_original = habit_match.group(1).strip() if habit_match else ""
        objetivo = goal_match.group(1).strip() if goal_match else ""
        objetivo = re.sub(r'^[^a-zA-ZáéíóúÁÉÍÓÚñÑ]+\s*', '', objetivo)
        habito_frases = {
            "Menos de 1 mes": "desde hace menos de un mes",
            "1-3 meses": "desde hace 1 a 3 meses",
            "3-6 meses": "desde hace 3 a 6 meses",
            "6-12 meses": "desde hace 6 a 12 meses",
            "Más de 1 año": "desde hace más de un año"
        }
        habito_redactado = habito_frases.get(habito_original, "")
        activity_summary = (
            f"La paciente refiere realizar actividad física regular con una frecuencia de {frecuencia}, "
            f"sesiones de {duracion} minutos"
        )
        if habito_redactado:
            activity_summary += f", manteniendo este hábito {habito_redactado}"
        activity_summary += f" con el objetivo de {objetivo.lower()}."
        summary_parts.append(activity_summary)
    else:
        summary_parts.append("Niega realizar actividad física de forma regular.")
    smoking, alcohol, substances = user_data.get('habits_smoking', 'No'), user_data.get('habits_alcohol', 'No'), user_data.get('habits_substance_use', 'No')
    
    # Construir texto de hábitos de forma más fluida
    habits_text = ""
    if smoking.lower() == 'no' and alcohol.lower() == 'no':
        # Caso especial: no fuma ni consume alcohol
        habits_text = "Manifiesta no fumar y tampoco consume alcohol"
        if substances.lower() == 'no':
            habits_text += ", y niega el uso de otras sustancias."
        else:
            habits_text += f", y refiere uso de otras sustancias ({substances})."
    else:
        # Caso general: construir lista de hábitos
        substance_parts = []
        if smoking.lower() != 'no':
            substance_parts.append(f"fuma ({smoking})")
        else:
            substance_parts.append("no fuma")
        
        if alcohol.lower() == 'ocasional':
            substance_parts.append("consume alcohol ocasionalmente")
        elif alcohol.lower() != 'no':
            substance_parts.append(f"consume alcohol ({alcohol})")
        else:
            substance_parts.append("no consume alcohol")
        
        if substances.lower() == 'no':
            substance_parts.append("niega el uso de otras sustancias")
        else:
            substance_parts.append(f"refiere uso de otras sustancias ({substances})")
        
        habits_text = f"En cuanto a hábitos: {', '.join(substance_parts)}."
    
    summary_parts.append(habits_text)
    return " ".join(summary_parts)

async def generate_summaries(update: Update, context: ContextTypes.DEFAULT_TYPE, node: dict):
    logger.info("Generando resúmenes de texto finales...")
    user_data = context.user_data
    
    # Generar summary del examen funcional solo si hay datos
    functional_exam_summary = _build_functional_exam_summary(user_data)
    if functional_exam_summary is not None:
        user_data['summary_functional_exam'] = functional_exam_summary
    # Si es None, no guardamos el summary (no se incluirá en el PDF)
    
    user_data['summary_habits'] = _build_habits_summary(user_data)
    user_data['summary_gyn_obstetric'] = _build_gyn_summary(user_data)
    return node.get('next_node')