"""
Script para IMPORTAR Y REEMPLAZAR completamente la base de datos en PythonAnywhere
⚠️ ADVERTENCIA: Esto REEMPLAZARÁ todos los datos de producción con los de desarrollo
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

# Ruta al archivo exportado
EXPORT_FILE = Path(__file__).parent.parent / "database_export.json"

if not EXPORT_FILE.exists():
    print(f"❌ Archivo de exportación no encontrado: {EXPORT_FILE}")
    print("💡 Primero ejecuta: python scripts/export_database.py")
    sys.exit(1)

print(f"📦 Importando datos desde: {EXPORT_FILE}")
print("⚠️  ADVERTENCIA: Esto REEMPLAZARÁ todos los datos existentes")
response = input("¿Estás seguro? Escribe 'SI' para continuar: ")
if response != 'SI':
    print("❌ Operación cancelada")
    sys.exit(0)

# Cargar datos
with open(EXPORT_FILE, 'r', encoding='utf-8') as f:
    exported_data = json.load(f)

async def clear_and_import_table(table_name: str, data: list):
    """Limpia la tabla y luego importa los datos"""
    if not data:
        print(f"⚠️  {table_name}: sin datos para importar")
        return 0
    
    try:
        # PRIMERO: Limpiar la tabla (DELETE)
        async with engine.begin() as conn:
            await conn.execute(text(f"DELETE FROM {table_name}"))
        print(f"🗑️  {table_name}: tabla limpiada")
        
        # SEGUNDO: Insertar nuevos datos
        inserted = 0
        for row in data:
            try:
                # Construir columnas y valores
                columns = list(row.keys())
                placeholders = ', '.join(['?' for _ in columns])
                column_names = ', '.join(columns)
                values = [row[col] for col in columns]
                
                async with engine.begin() as conn:
                    await conn.execute(
                        text(f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"),
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
    # Primero las tablas sin dependencias, luego las que dependen de ellas
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
    
    print("\n🔄 Iniciando reemplazo completo de base de datos...")
    print("=" * 60)
    
    for table in IMPORT_ORDER:
        if table in exported_data:
            count = await clear_and_import_table(table, exported_data[table])
            total_imported += count
    
    print("=" * 60)
    print(f"\n✅ Reemplazo completado: {total_imported} registros totales")
    print("💡 La base de datos de producción ahora tiene los mismos datos que desarrollo")

if __name__ == "__main__":
    asyncio.run(main())

