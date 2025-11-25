"""
Script para exportar solo tablas específicas (galería, precios, etc.)
Útil cuando solo quieres sincronizar ciertos datos
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

# Tablas específicas a exportar (modifica según necesites)
TABLES_TO_EXPORT = [
    'gallery',      # Items de galería
    'precios',      # Información de precios
    # 'faqs',       # Descomenta si también quieres FAQs
    # 'locations',  # Descomenta si también quieres ubicaciones
    # 'text_content', # Descomenta si también quieres contenido de texto
]

print(f"📦 Exportando tablas específicas de: {DB_PATH}")
print(f"📋 Tablas: {', '.join(TABLES_TO_EXPORT)}")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

exported_data = {}

for table in TABLES_TO_EXPORT:
    try:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        if rows:
            data = [dict(row) for row in rows]
            exported_data[table] = data
            print(f"✅ {table}: {len(data)} registros")
        else:
            print(f"⚠️  {table}: vacía")
    except sqlite3.OperationalError as e:
        if "no such table" in str(e).lower():
            print(f"⚠️  {table}: tabla no existe")
        else:
            print(f"❌ Error en {table}: {e}")

conn.close()

# Guardar en JSON
output_file = Path(__file__).parent.parent / "database_export_partial.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(exported_data, f, indent=2, default=str, ensure_ascii=False)

print(f"\n✅ Datos exportados a: {output_file}")
print(f"📊 Total de tablas exportadas: {len(exported_data)}")

