import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parents[1]))

DB_PATH = "database/medical_bot.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("=" * 80)
print("LIMPIEZA DE MENSAJES DE BIENVENIDA")
print("=" * 80)

# Mostrar mensajes actuales
cursor = conn.execute(
    "SELECT bot_id, value FROM text_content WHERE key = ? ORDER BY bot_id",
    ("msg_bienvenida_editable",)
)

rows = cursor.fetchall()
print(f"\n📋 Mensajes actuales en la BD:")
for row in rows:
    value = row['value']
    print(f"  bot_id={row['bot_id']}: '{value[:50]}...' (longitud: {len(value)})")

# Preguntar qué bot_id limpiar
print("\n" + "=" * 80)
bot_id = input("¿Qué bot_id quieres limpiar? (presiona Enter para cancelar): ").strip()

if not bot_id:
    print("❌ Operación cancelada")
    conn.close()
    sys.exit(0)

try:
    bot_id = int(bot_id)
except ValueError:
    print("❌ Error: bot_id debe ser un número")
    conn.close()
    sys.exit(1)

# Confirmar
cursor = conn.execute(
    "SELECT value FROM text_content WHERE key = ? AND bot_id = ?",
    ("msg_bienvenida_editable", bot_id)
)
row = cursor.fetchone()

if not row:
    print(f"❌ No se encontró mensaje para bot_id={bot_id}")
    conn.close()
    sys.exit(1)

print(f"\n⚠️  Mensaje actual para bot_id={bot_id}:")
print(f"   '{row['value']}'")
print(f"\n¿Estás seguro de que quieres ELIMINAR este mensaje? (s/n): ", end="")
confirm = input().strip().lower()

if confirm != 's':
    print("❌ Operación cancelada")
    conn.close()
    sys.exit(0)

# Eliminar
conn.execute(
    "DELETE FROM text_content WHERE key = ? AND bot_id = ?",
    ("msg_bienvenida_editable", bot_id)
)
conn.commit()

print(f"✅ Mensaje eliminado para bot_id={bot_id}")

# Verificar
cursor = conn.execute(
    "SELECT value FROM text_content WHERE key = ? AND bot_id = ?",
    ("msg_bienvenida_editable", bot_id)
)
row = cursor.fetchone()

if row:
    print(f"⚠️  ADVERTENCIA: Aún existe un mensaje para bot_id={bot_id}: '{row['value']}'")
else:
    print(f"✅ Confirmado: No hay mensaje para bot_id={bot_id}")

conn.close()
print("\n" + "=" * 80)
print("✅ Limpieza completada")
print("=" * 80)

