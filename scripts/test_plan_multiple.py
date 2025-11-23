#!/usr/bin/env python3
"""Script para probar el parsing de múltiples items sin marcadores"""

import re

# Simular el plan como se guarda cuando el doctor añade items uno por uno
# (sin marcadores, solo saltos de línea)
plan_text = """Prevención vacunación para VPH: Gardasil 4 o Gardasil 9 por 3 dosis
Realizar ejercicios de bajo impacto
Evaluación ginecológica anual.
Iniciar Anticonceptivos: Genesa 20 ® tomar 1 comprimido el primer día de la menstruación todos los días a la misma hora durante 28 días. Iniciar la segunda caja el primer día de menstruación del próximo ciclo.
Pendiente resultados de citología
Usar jabón intimo con ph neutro"""

print("="*80)
print("PLAN ORIGINAL (6 items sin marcadores):")
print(plan_text)
print("="*80)

# Método actual (PROBLEMÁTICO)
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

print(f"\n❌ MÉTODO ACTUAL:")
print(f"Items detectados: {len(plan_items)} (Esperado: 6)")
print(f"Tiene marcadores: {has_markers}")
for i, item in enumerate(plan_items, 1):
    print(f"  {i}. {item[:80]}...")

# Método corregido: si no hay marcadores, dividir por saltos de línea
print(f"\n✅ MÉTODO CORREGIDO:")
if not has_markers:
    # Si no hay marcadores, cada línea es un item separado
    plan_items_correct = [line.strip() for line in plan_text.strip().split('\n') if line.strip()]
else:
    plan_items_correct = plan_items

print(f"Items detectados: {len(plan_items_correct)} (Esperado: 6)")
for i, item in enumerate(plan_items_correct, 1):
    print(f"  {i}. {item[:80]}...")

