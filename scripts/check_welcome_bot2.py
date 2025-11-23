import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parents[1]))

DB_PATH = "database/medical_bot.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Verificar registros para bot_id=2
cursor = conn.execute(
    "SELECT COUNT(*) as count FROM text_content WHERE key = ? AND bot_id = ?",
    ("msg_bienvenida_editable", 2)
)
row = cursor.fetchone()
print(f"Registros para bot_id=2: {row['count']}")

# Obtener el valor
cursor = conn.execute(
    "SELECT value FROM text_content WHERE key = ? AND bot_id = ?",
    ("msg_bienvenida_editable", 2)
)
row = cursor.fetchone()
if row:
    print(f"Valor: '{row['value']}'")
    print(f"Longitud: {len(row['value'])}")
else:
    print("No encontrado")

conn.close()

