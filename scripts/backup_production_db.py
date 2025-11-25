"""
Script para hacer BACKUP de la base de datos de producción ANTES de reemplazarla
Ejecuta esto PRIMERO en el servidor antes de importar datos de desarrollo
"""
import sqlite3
import json
import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path para importar módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Ruta a la base de datos de producción
# Ajusta esta ruta según tu configuración en PythonAnywhere
DB_PATH = Path(__file__).parent.parent / "database" / "medical_bot.db"

if not DB_PATH.exists():
    print(f"❌ Base de datos no encontrada en: {DB_PATH}")
    sys.exit(1)

# Crear nombre de backup con timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = Path(__file__).parent.parent / f"database_backup_{timestamp}.json"

print(f"📦 Haciendo backup de: {DB_PATH}")
print(f"💾 Guardando en: {backup_file}")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Tablas importantes a respaldar
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

backup_data = {
    '_metadata': {
        'backup_date': datetime.now().isoformat(),
        'source': 'production',
        'tables_count': len(TABLES)
    }
}

for table in TABLES:
    try:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        if rows:
            data = [dict(row) for row in rows]
            backup_data[table] = data
            print(f"✅ {table}: {len(data)} registros respaldados")
        else:
            print(f"⚠️  {table}: vacía")
    except sqlite3.OperationalError as e:
        if "no such table" in str(e).lower():
            print(f"⚠️  {table}: tabla no existe (puede ser normal)")
        else:
            print(f"❌ Error en {table}: {e}")

conn.close()

# Guardar backup
with open(backup_file, 'w', encoding='utf-8') as f:
    json.dump(backup_data, f, indent=2, default=str, ensure_ascii=False)

print(f"\n✅ Backup completado: {backup_file}")
print(f"📊 Total de tablas respaldadas: {len([t for t in TABLES if t in backup_data])}")
print(f"\n💡 Guarda este archivo en un lugar seguro antes de reemplazar la BD")

