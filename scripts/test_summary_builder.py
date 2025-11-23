#!/usr/bin/env python3
"""
Script de prueba para build_narrative_summary
Prueba diferentes escenarios del resumen médico
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.pdf.summary_builder import build_narrative_summary

def test_scenario(name, report_data):
    """Prueba un escenario específico"""
    print(f"\n{'='*80}")
    print(f"📋 ESCENARIO: {name}")
    print(f"{'='*80}")
    
    result = build_narrative_summary(report_data)
    narrative = result.get('narrative_summary', '')
    
    print(f"\n📄 RESULTADO:")
    print(f"{'-'*80}")
    # Reemplazar <br/> con saltos de línea para mejor visualización
    display_text = narrative.replace('<br/>', '\n').replace('<ul>', '\n<ul>').replace('</ul>', '</ul>\n')
    print(display_text)
    print(f"{'-'*80}")
    
    # Verificaciones
    checks = []
    if 'por presentar control' in narrative.lower():
        checks.append("❌ ERROR: Todavía usa 'por presentar' para control")
    elif 'a control' in narrative.lower():
        checks.append("✅ CORRECTO: Usa 'a control'")
    
    if 'manifiesta niega dismenorrea' in narrative.lower():
        checks.append("❌ ERROR: Todavía usa 'manifiesta niega'")
    elif 'no presentar dismenorrea' in narrative.lower():
        checks.append("✅ CORRECTO: Usa 'no presentar dismenorrea'")
    
    if '<ul>' in narrative and '<li>' in narrative:
        checks.append("✅ CORRECTO: Tiene etiquetas HTML <ul> y <li>")
    else:
        checks.append("❌ ERROR: No tiene etiquetas HTML correctas")
    
    if checks:
        print(f"\n🔍 VERIFICACIONES:")
        for check in checks:
            print(f"  {check}")
    
    return narrative

# Escenario 1: Caso Básico - Control Ginecológico Normal
scenario_1 = {
    'full_name': 'María González',
    'age': '28',
    'ci': '12345678',
    'reason_for_visit': 'control ginecológico',
    'gyn_dysmenorrhea': 'No',
    'functional_dispareunia': 'No',
    'functional_dischezia': 'No',
    'gyn_fertility_intent': 'Sin deseo de fertilidad',
    'admin_ultrasound': 'Útero ambos ovarios sin patología estructural',
    'admin_diagnosis': 'Control ginecológico normal',
    'admin_plan': 'Iniciar Anticonceptivos: Genesa 20 ® tomar 1 comprimido el primer día de la menstruación todos los días a la misma hora durante 28 días. Iniciar la segunda caja el primer día de menstruación del próximo ciclo.\nPrevención vacunación para VPH: Gardasil 4 o Gardasil 9 por 3 dosis'
}

# Escenario 2: Con Dismenorrea Moderada
scenario_2 = {
    'full_name': 'Ana Pérez',
    'age': '32',
    'ci': '87654321',
    'reason_for_visit': 'dolor pélvico',
    'gyn_dysmenorrhea': 'Sí, intensidad: 5/10',
    'functional_dispareunia': 'No',
    'functional_dischezia': 'No',
    'gyn_fertility_intent': 'Sin deseo de fertilidad',
    'admin_ultrasound': 'Útero con miomas pequeños',
    'admin_diagnosis': 'Dismenorrea funcional',
    'admin_plan': 'Analgésicos antiinflamatorios durante la menstruación\nControl en 3 meses'
}

# Escenario 3: Con Dispareunia Severa
scenario_3 = {
    'full_name': 'Laura Martínez',
    'age': '35',
    'ci': '11223344',
    'reason_for_visit': 'dolor durante las relaciones sexuales',
    'gyn_dysmenorrhea': 'No',
    'functional_dispareunia': 'Sí, tipo profundo (Intensidad: 8/10)',
    'functional_dischezia': 'No',
    'gyn_fertility_intent': 'Sin deseo de fertilidad',
    'admin_ultrasound': 'Endometriosis en ovarios',
    'admin_diagnosis': 'Endometriosis\nDispareunia secundaria',
    'admin_plan': 'Tratamiento hormonal\nFisioterapia del suelo pélvico\nControl en 6 meses'
}

# Escenario 4: Con Disquecia Eventual
scenario_4 = {
    'full_name': 'Carmen López',
    'age': '30',
    'ci': '55667788',
    'reason_for_visit': 'dolor al evacuar',
    'gyn_dysmenorrhea': 'No',
    'functional_dispareunia': 'No',
    'functional_dischezia': 'Eventual',
    'gyn_fertility_intent': 'Sin deseo de fertilidad',
    'admin_ultrasound': 'Endometriosis profunda',
    'admin_diagnosis': 'Endometriosis profunda con afectación rectosigmoidea',
    'admin_plan': 'Estudio de extensión con resonancia magnética\nEvaluación quirúrgica'
}

# Escenario 5: Con Deseo de Fertilidad No Logrado
scenario_5 = {
    'full_name': 'Sofía Rodríguez',
    'age': '29',
    'ci': '99887766',
    'reason_for_visit': 'infertilidad',
    'gyn_dysmenorrhea': 'Sí, intensidad: 7/10',
    'functional_dispareunia': 'Sí, tipo profundo (Intensidad: 5/10)',
    'functional_dischezia': 'No',
    'gyn_fertility_intent': 'Con deseo de fertilidad no logrado',
    'admin_ultrasound': 'Quistes endometriósicos bilaterales',
    'admin_diagnosis': 'Endometriosis\nInfertilidad secundaria',
    'admin_plan': 'Laparoscopia diagnóstica y terapéutica\nEstudio de fertilidad de pareja\nAsesoramiento reproductivo'
}

# Ejecutar pruebas
if __name__ == '__main__':
    print("🧪 PRUEBAS DEL RESUMEN MÉDICO (build_narrative_summary)")
    print("="*80)
    
    test_scenario("1. Caso Básico - Control Ginecológico Normal", scenario_1)
    test_scenario("2. Con Dismenorrea Moderada", scenario_2)
    test_scenario("3. Con Dispareunia Severa", scenario_3)
    test_scenario("4. Con Disquecia Eventual", scenario_4)
    test_scenario("5. Con Deseo de Fertilidad No Logrado", scenario_5)
    
    print(f"\n{'='*80}")
    print("✅ PRUEBAS COMPLETADAS")
    print(f"{'='*80}")

