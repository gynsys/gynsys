"""
Script para verificar el estado de las ubicaciones y sus días de atención.
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'medical_bot.db')

print(f"Conectando a: {DB_PATH}\n")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Verificar estructura de la tabla
print("=== ESTRUCTURA DE LA TABLA ===")
cursor.execute("PRAGMA table_info(locations)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Ver todas las ubicaciones
print("\n=== UBICACIONES EN LA BASE DE DATOS ===")
cursor.execute("SELECT id, name, open_days FROM locations")
locations = cursor.fetchall()

if not locations:
    print("  No hay ubicaciones registradas.")
else:
    for loc in locations:
        loc_id, name, open_days = loc
        print(f"  ID: {loc_id} | Nombre: {name} | open_days: {open_days}")

conn.close()
print("\nScript completado.")
