"""
Script temporal para añadir la columna open_days a la tabla locations.
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'medical_bot.db')

print(f"Conectando a: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Verificar si la columna ya existe
cursor.execute("PRAGMA table_info(locations)")
columns = [row[1] for row in cursor.fetchall()]

if 'open_days' in columns:
    print("✅ La columna 'open_days' ya existe.")
else:
    print("➕ Añadiendo columna 'open_days'...")
    cursor.execute("ALTER TABLE locations ADD COLUMN open_days VARCHAR DEFAULT '0,1,2,3,4'")
    conn.commit()
    print("✅ Columna añadida exitosamente.")

conn.close()
print("🎉 Script completado.")
