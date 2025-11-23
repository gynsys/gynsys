#!/usr/bin/env python3
"""Script para verificar que la corrección del parsing del plan funciona"""

import re

# Simular el plan como se guarda en la BD (con saltos de línea dentro de items)
plan_text = """-Iniciar Anticonceptivos: Genesa 20 ® tomar 1 comprimido el primer día de la menstruación 
todos los días a la misma hora durante 28 días. Iniciar la segunda caja el primer día de 
menstruación del próximo ciclo.

-Prevención vacunación para VPH: Gardasil 4 o Gardasil 9 por 3 dosis"""

print("="*80)
print("PLAN ORIGINAL:")
print(plan_text)
print("="*80)

# Aplicar la lógica corregida
pattern = r'^[-•]\s*|^\d+[.)]\s*'
lines = plan_text.strip().split('\n')
plan_items = []
current_item = []

for line in lines:
    line = line.strip()
    if not line:
        continue
    
    # Si la línea empieza con un marcador de item nuevo
    if re.match(pattern, line):
        # Guardar el item anterior si existe
        if current_item:
            plan_items.append(' '.join(current_item))
        # Iniciar nuevo item
        current_item = [line]
    else:
        # Continuar el item actual (es una continuación de la línea anterior)
        if current_item:
            current_item.append(line)
        else:
            # Si no hay item actual, crear uno nuevo (caso edge)
            current_item = [line]

# Guardar el último item
if current_item:
    plan_items.append(' '.join(current_item))

# Si no se detectaron items con marcadores, usar el método simple (fallback)
if not plan_items:
    plan_items = [p.strip() for p in plan_text.strip().split('\n') if p.strip()]

print(f"\n✅ Items detectados: {len(plan_items)}")
for i, item in enumerate(plan_items, 1):
    print(f"\n  {i}. {item}")

# Formatear con viñetas
bullet_list_parts = []
for item in plan_items:
    # Quitamos viñetas manuales si el usuario las puso (como '•' o '-')
    cleaned_item = re.sub(r'^[•*-]\s*|^\d+[.)]\s*', '', item)
    # Agregar viñeta • con espacio y salto de línea
    bullet_list_parts.append(f"•&nbsp;&nbsp;{cleaned_item}")

plan_formatted = "<br/>".join(bullet_list_parts)

print("\n" + "="*80)
print("PLAN FORMATEADO PARA PDF:")
print(plan_formatted.replace("&nbsp;", " ").replace("<br/>", "\n"))
print("="*80)

