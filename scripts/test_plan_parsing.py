#!/usr/bin/env python3
"""Script para probar el parsing del plan y detectar el problema"""

# Simular el plan como se guarda en la BD (con saltos de línea dentro de items)
plan_text = """-Iniciar Anticonceptivos: Genesa 20 ® tomar 1 comprimido el primer día de la menstruación 
todos los días a la misma hora durante 28 días. Iniciar la segunda caja el primer día de 
menstruación del próximo ciclo.

-Prevención vacunación para VPH: Gardasil 4 o Gardasil 9 por 3 dosis"""

print("="*80)
print("PLAN ORIGINAL:")
print(plan_text)
print("="*80)

# Método actual (INCORRECTO - divide por cada \n)
print("\n❌ MÉTODO ACTUAL (INCORRECTO):")
plan_items_incorrect = [p.strip() for p in plan_text.strip().split('\n') if p.strip()]
print(f"Items detectados: {len(plan_items_incorrect)}")
for i, item in enumerate(plan_items_incorrect, 1):
    print(f"  {i}. {item[:60]}...")

# Método correcto (detectar items por guiones/viñetas al inicio)
print("\n✅ MÉTODO CORRECTO:")
import re

# Dividir por líneas que empiezan con guión, viñeta o número
# Patrón: línea que empieza con -, •, o número seguido de ) o .
pattern = r'^[-•]\s*|^\d+[.)]\s*'
lines = plan_text.strip().split('\n')
plan_items_correct = []
current_item = []

for line in lines:
    line = line.strip()
    if not line:
        continue
    
    # Si la línea empieza con un marcador de item nuevo
    if re.match(pattern, line):
        # Guardar el item anterior si existe
        if current_item:
            plan_items_correct.append(' '.join(current_item))
        # Iniciar nuevo item
        current_item = [line]
    else:
        # Continuar el item actual
        if current_item:
            current_item.append(line)
        else:
            # Si no hay item actual, crear uno nuevo (caso edge)
            current_item = [line]

# Guardar el último item
if current_item:
    plan_items_correct.append(' '.join(current_item))

print(f"Items detectados: {len(plan_items_correct)}")
for i, item in enumerate(plan_items_correct, 1):
    print(f"  {i}. {item[:80]}...")

