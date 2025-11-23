import sqlite3
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parents[1]))

DB_PATH = "database/medical_bot.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

cursor = conn.execute(
    "SELECT key, bot_id, value FROM text_content WHERE key = ? ORDER BY bot_id",
    ("msg_bienvenida_editable",)
)

rows = cursor.fetchall()
print(f"Registros encontrados para 'msg_bienvenida_editable': {len(rows)}\n")

for row in rows:
    value = row['value']
    print(f"bot_id={row['bot_id']}")
    print(f"value (primeros 100 chars): {value[:100]}...")
    print(f"value (completo): {value}")
    print("-" * 80)

# Verificar si hay duplicados por bot_id
cursor = conn.execute(
    "SELECT bot_id, COUNT(*) as count FROM text_content WHERE key = ? GROUP BY bot_id HAVING COUNT(*) > 1",
    ("msg_bienvenida_editable",)
)

duplicates = cursor.fetchall()
if duplicates:
    print("\n⚠️ DUPLICADOS ENCONTRADOS:")
    for dup in duplicates:
        print(f"bot_id={dup['bot_id']} tiene {dup['count']} registros")
else:
    print("\n✅ No hay duplicados por bot_id")

conn.close()

