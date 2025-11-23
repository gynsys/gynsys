"""
Script para exportar datos de la base de datos local
Úsalo antes de migrar a PythonAnywhere
"""
import sqlite3
import json
import sys
from pathlib import Path

# Ruta a la base de datos
DB_PATH = Path(__file__).parent.parent / "database" / "medical_bot.db"

if not DB_PATH.exists():
    print(f"❌ Base de datos no encontrada en: {DB_PATH}")
    sys.exit(1)

print(f"📦 Exportando datos de: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Tablas importantes a exportar
TABLES = [
    'doctors',
    'bots',
    'user_tenants',
    'patient_doctor',
    'medical_histories',
    'citas',
    'text_content',
    'locations',
    'faqs',
    'consejos',
    'gallery',
    'diagnosticos',
    'precios',
    'main_menu_buttons',
    'submenus',
    'submenu_buttons',
    'notifications',
    'pdf_settings',
    'extra_modules',
    'test_questions',
    'bot_logos',
]

exported_data = {}

for table in TABLES:
    try:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        if rows:
            # Convertir rows a lista de diccionarios
            data = [dict(row) for row in rows]
            exported_data[table] = data
            print(f"✅ {table}: {len(data)} registros")
        else:
            print(f"⚠️  {table}: vacía")
    except sqlite3.OperationalError as e:
        if "no such table" in str(e).lower():
            print(f"⚠️  {table}: tabla no existe (puede ser normal)")
        else:
            print(f"❌ Error en {table}: {e}")

conn.close()

# Guardar en JSON
output_file = Path(__file__).parent.parent / "database_export.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(exported_data, f, indent=2, default=str, ensure_ascii=False)

print(f"\n✅ Datos exportados a: {output_file}")
print(f"📊 Total de tablas exportadas: {len([t for t in TABLES if t in exported_data])}")

