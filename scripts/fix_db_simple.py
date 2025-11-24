"""
Script simple para reparar base de datos SQLite corrupta
"""
import sqlite3
import shutil
from pathlib import Path

DB_PATH = "database/medical_bot.db"
BACKUP_PATH = "database/medical_bot.db.backup"

print("🔍 Verificando base de datos...")

# Crear backup
if Path(DB_PATH).exists():
    print(f"📦 Creando backup: {BACKUP_PATH}")
    shutil.copy2(DB_PATH, BACKUP_PATH)

# Intentar reparar con dump
print("🔧 Reparando base de datos...")
try:
    # Conectar y hacer dump
    old_conn = sqlite3.connect(DB_PATH)
    
    # Crear nueva base de datos
    new_db = "database/medical_bot.db.new"
    new_conn = sqlite3.connect(new_db)
    
    # Hacer dump y restore
    for line in old_conn.iterdump():
        new_conn.executescript(line)
    
    new_conn.close()
    old_conn.close()
    
    # Reemplazar
    Path(DB_PATH).unlink()
    Path(new_db).rename(DB_PATH)
    
    print("✅ Base de datos reparada!")
    print(f"📦 Backup en: {BACKUP_PATH}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 La base de datos está muy corrupta.")
    print("   Necesitas descargar una copia fresca desde producción.")

