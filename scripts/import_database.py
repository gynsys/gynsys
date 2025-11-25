"""
Script para importar datos a la base de datos en PythonAnywhere
Úsalo después de exportar desde la base local
"""
import json
import sys
import asyncio
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from database.engine import engine
from database.session import get_session

# Ruta al archivo exportado
EXPORT_FILE = Path(__file__).parent.parent / "database_export.json"

if not EXPORT_FILE.exists():
    print(f"❌ Archivo de exportación no encontrado: {EXPORT_FILE}")
    print("💡 Primero ejecuta: python scripts/export_database.py")
    sys.exit(1)

print(f"📦 Importando datos desde: {EXPORT_FILE}")

# Cargar datos
with open(EXPORT_FILE, 'r', encoding='utf-8') as f:
    exported_data = json.load(f)

async def import_table(table_name: str, data: list):
    """Importa datos de una tabla"""
    if not data:
        print(f"⚠️  {table_name}: sin datos")
        return 0
    
    async with get_session() as session:
        try:
            # Obtener columnas de la tabla
            async with engine.begin() as conn:
                result = await conn.execute(
                    text(f"PRAGMA table_info({table_name})")
                )
                columns = [row[1] for row in result.fetchall()]
            
            if not columns:
                print(f"⚠️  {table_name}: tabla no existe o está vacía")
                return 0
            
            # Construir INSERT
            placeholders = ', '.join(['?' for _ in columns])
            column_names = ', '.join(columns)
            
            inserted = 0
            for row in data:
                try:
                    # Filtrar solo las columnas que existen
                    values = [row.get(col) for col in columns]
                    
                    async with engine.begin() as conn:
                        await conn.execute(
                            text(f"INSERT OR IGNORE INTO {table_name} ({column_names}) VALUES ({placeholders})"),
                            values
                        )
                    inserted += 1
                except Exception as e:
                    print(f"  ⚠️  Error insertando fila en {table_name}: {e}")
                    continue
            
            print(f"✅ {table_name}: {inserted}/{len(data)} registros importados")
            return inserted
            
        except Exception as e:
            print(f"❌ Error importando {table_name}: {e}")
            return 0

async def main():
    """Función principal de importación"""
    total_imported = 0
    
    # Orden de importación importante (respetar foreign keys)
    IMPORT_ORDER = [
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
    
    for table in IMPORT_ORDER:
        if table in exported_data:
            count = await import_table(table, exported_data[table])
            total_imported += count
    
    print(f"\n✅ Importación completada: {total_imported} registros totales")

if __name__ == "__main__":
    asyncio.run(main())

