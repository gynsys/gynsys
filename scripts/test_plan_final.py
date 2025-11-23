#!/usr/bin/env python3
"""Script final para probar el parsing del plan con espacios vacíos"""

import re

# Caso 1: Un solo item con espacios vacíos (el problema reportado)
plan_text_1 = """Iniciar Anticonceptivos: Genesa 20 ® tomar 1 comprimido el primer día de la menstruación 



todos los días a la misma hora durante 28 días. Iniciar la segunda caja el primer día de 

menstruación del próximo ciclo."""

# Caso 2: Múltiples items con marcadores
plan_text_2 = """-Iniciar Anticonceptivos: Genesa 20 ® tomar 1 comprimido el primer día de la menstruación 
todos los días a la misma hora durante 28 días. Iniciar la segunda caja el primer día de 
menstruación del próximo ciclo.

-Prevención vacunación para VPH: Gardasil 4 o Gardasil 9 por 3 dosis"""

# Caso 3: Múltiples items sin marcadores (edge case)
plan_text_3 = """Iniciar Anticonceptivos: Genesa 20 ®
Prevención vacunación para VPH: Gardasil 4"""

def parse_plan(plan_text):
    """Aplica la lógica corregida"""
    pattern = r'^[-•]\s*|^\d+[.)]\s*'
    lines = plan_text.strip().split('\n')
    plan_items = []
    current_item = []
    has_markers = False
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            continue
        
        if re.match(pattern, stripped):
            has_markers = True
            if current_item:
                plan_items.append(' '.join(current_item))
            current_item = [stripped]
        else:
            if current_item:
                current_item.append(stripped)
            else:
                current_item = [stripped]
    
    if current_item:
        plan_items.append(' '.join(current_item))
    
    return plan_items, has_markers

print("="*80)
print("CASO 1: Un solo item con espacios vacíos")
print("="*80)
items_1, markers_1 = parse_plan(plan_text_1)
print(f"Items detectados: {len(items_1)} (Esperado: 1)")
print(f"Tiene marcadores: {markers_1}")
for i, item in enumerate(items_1, 1):
    print(f"  {i}. {item[:100]}...")

print("\n" + "="*80)
print("CASO 2: Múltiples items con marcadores")
print("="*80)
items_2, markers_2 = parse_plan(plan_text_2)
print(f"Items detectados: {len(items_2)} (Esperado: 2)")
print(f"Tiene marcadores: {markers_2}")
for i, item in enumerate(items_2, 1):
    print(f"  {i}. {item[:100]}...")

print("\n" + "="*80)
print("CASO 3: Múltiples items sin marcadores (edge case)")
print("="*80)
items_3, markers_3 = parse_plan(plan_text_3)
print(f"Items detectados: {len(items_3)} (Esperado: 2)")
print(f"Tiene marcadores: {markers_3}")
for i, item in enumerate(items_3, 1):
    print(f"  {i}. {item[:100]}...")

