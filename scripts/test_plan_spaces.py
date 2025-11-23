#!/usr/bin/env python3
"""Script para probar el manejo de espacios vacíos en el plan"""

import re

# Caso problemático: un solo item con líneas vacías dentro
plan_text = """Iniciar Anticonceptivos: Genesa 20 ® tomar 1 comprimido el primer día de la menstruación 



todos los días a la misma hora durante 28 días. Iniciar la segunda caja el primer día de 

menstruación del próximo ciclo."""

print("="*80)
print("PLAN ORIGINAL (1 item con espacios vacíos):")
print(repr(plan_text))
print("="*80)

# Método actual (PROBLEMÁTICO)
print("\n❌ MÉTODO ACTUAL (PROBLEMÁTICO):")
pattern = r'^[-•]\s*|^\d+[.)]\s*'
lines = plan_text.strip().split('\n')
plan_items_old = []
current_item = []

for line in lines:
    line = line.strip()
    if not line:
        continue  # Salta líneas vacías, pero esto puede causar problemas
    
    if re.match(pattern, line):
        if current_item:
            plan_items_old.append(' '.join(current_item))
        current_item = [line]
    else:
        if current_item:
            current_item.append(line)
        else:
            current_item = [line]

if current_item:
    plan_items_old.append(' '.join(current_item))

print(f"Items detectados: {len(plan_items_old)}")
for i, item in enumerate(plan_items_old, 1):
    print(f"  {i}. {item[:80]}...")

# Método mejorado: agrupar líneas consecutivas sin marcador
print("\n✅ MÉTODO MEJORADO:")
pattern = r'^[-•]\s*|^\d+[.)]\s*'
lines = plan_text.strip().split('\n')
plan_items_new = []
current_item = []
empty_line_count = 0

for line in lines:
    stripped = line.strip()
    
    # Si la línea está vacía, incrementar contador
    if not stripped:
        empty_line_count += 1
        # Si hay más de 1 línea vacía consecutiva, podría ser separador real
        # Pero en este caso, seguimos agrupando como parte del mismo item
        continue
    
    # Si encontramos un marcador de nuevo item
    if re.match(pattern, stripped):
        # Guardar item anterior si existe
        if current_item:
            plan_items_new.append(' '.join(current_item))
        # Iniciar nuevo item
        current_item = [stripped]
        empty_line_count = 0
    else:
        # Es continuación del item actual (con o sin líneas vacías previas)
        # Si había líneas vacías, las ignoramos (son parte del formato)
        if current_item:
            current_item.append(stripped)
        else:
            # Primer item sin marcador explícito
            current_item = [stripped]
        empty_line_count = 0

# Guardar último item
if current_item:
    plan_items_new.append(' '.join(current_item))

print(f"Items detectados: {len(plan_items_new)}")
for i, item in enumerate(plan_items_new, 1):
    print(f"  {i}. {item[:80]}...")

