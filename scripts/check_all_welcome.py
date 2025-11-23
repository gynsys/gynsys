import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parents[1]))

DB_PATH = "database/medical_bot.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("=" * 80)
print("TODOS LOS MENSAJES DE BIENVENIDA EN LA BD")
print("=" * 80)

cursor = conn.execute(
    "SELECT bot_id, key, value, LENGTH(value) as length FROM text_content WHERE key = ? ORDER BY bot_id",
    ("msg_bienvenida_editable",)
)

rows = cursor.fetchall()
print(f"\n📋 Total de registros: {len(rows)}\n")

for row in rows:
    value = row['value']
    print(f"bot_id={row['bot_id']}:")
    print(f"  key: {row['key']}")
    print(f"  length: {row['length']}")
    print(f"  value (primeros 100 chars): {value[:100]}...")
    print(f"  value (completo): {value}")
    print("-" * 80)

conn.close()

