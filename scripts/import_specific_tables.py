"""
Script para importar solo tablas específicas desde database_export_partial.json
"""
import json
import sys
import asyncio
from pathlib import Path
from sqlalchemy import text
from database.engine import engine

# Ruta al archivo exportado
EXPORT_FILE = Path(__file__).parent.parent / "database_export_partial.json"

if not EXPORT_FILE.exists():
    print(f"❌ Archivo de exportación no encontrado: {EXPORT_FILE}")
    print("💡 Primero ejecuta: python scripts/export_specific_tables.py")
    sys.exit(1)

print(f"📦 Importando datos desde: {EXPORT_FILE}")

# Cargar datos
with open(EXPORT_FILE, 'r', encoding='utf-8') as f:
    exported_data = json.load(f)

async def import_table(table_name: str, data: list):
    """Importa datos de una tabla (INSERT OR REPLACE para actualizar existentes)"""
    if not data:
        print(f"⚠️  {table_name}: sin datos")
        return 0
    
    try:
        inserted = 0
        for row in data:
            try:
                # Construir columnas y valores
                columns = list(row.keys())
                placeholders = ', '.join(['?' for _ in columns])
                column_names = ', '.join(columns)
                values = [row[col] for col in columns]
                
                # Usar INSERT OR REPLACE para actualizar si existe
                async with engine.begin() as conn:
                    await conn.execute(
                        text(f"INSERT OR REPLACE INTO {table_name} ({column_names}) VALUES ({placeholders})"),
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
    
    for table, data in exported_data.items():
        count = await import_table(table, data)
        total_imported += count
    
    print(f"\n✅ Importación completada: {total_imported} registros totales")
    print("💡 Los registros existentes fueron actualizados (INSERT OR REPLACE)")

if __name__ == "__main__":
    asyncio.run(main())

