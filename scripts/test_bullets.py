#!/usr/bin/env python3
"""Script rápido para probar el formato de viñetas en el plan"""

# Simular el contenido del plan
plan_text = """Iniciar Anticonceptivos: Genesa 20 ® tomar 1 comprimido el primer día de la menstruación todos los días a la misma hora durante 28 días. Iniciar la segunda caja el primer día de menstruación del próximo ciclo.
Prevención vacunación para VPH: Gardasil 4 o Gardasil 9 por 3 dosis"""

# Simular el procesamiento
import re

plan_items = [p.strip() for p in plan_text.strip().split('\n') if p.strip()]

bullet_list_parts = []
for item in plan_items:
    # Quitamos viñetas manuales si el usuario las puso (como '•' o '-')
    cleaned_item = re.sub(r'^[•*-]\s*', '', item)
    # Agregar viñeta • con espacio y salto de línea
    bullet_list_parts.append(f"•&nbsp;&nbsp;{cleaned_item}")

# Unir los ítems con saltos de línea
plan_formatted_as_list = "<br/>".join(bullet_list_parts)

print("Plan formateado:")
print(plan_formatted_as_list)
print("\n" + "="*80)
print("\nVista HTML (simulada):")
print(plan_formatted_as_list.replace("&nbsp;", " ").replace("<br/>", "\n"))

