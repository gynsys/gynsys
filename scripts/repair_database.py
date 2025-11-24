"""
Script para verificar y reparar una base de datos SQLite corrupta
"""
import sqlite3
import sys
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import DB_PATH

def repair_database(db_path: str):
    """Intenta reparar una base de datos SQLite corrupta"""
    db_file = Path(db_path)
    
    if not db_file.exists():
        print(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    print(f"🔍 Verificando base de datos: {db_path}")
    
    # 1. Verificar integridad
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ejecutar integridad check
        print("📋 Verificando integridad...")
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        if result[0] == "ok":
            print("✅ Base de datos está intacta")
            conn.close()
            return True
        else:
            print(f"⚠️ Problemas detectados: {result[0]}")
            conn.close()
    except sqlite3.DatabaseError as e:
        print(f"❌ Error al verificar: {e}")
    
    # 2. Intentar reparar con dump y restore
    print("\n🔧 Intentando reparar la base de datos...")
    
    backup_path = str(db_file) + ".backup"
    repaired_path = str(db_file) + ".repaired"
    
    try:
        # Crear backup del archivo corrupto
        print(f"📦 Creando backup: {backup_path}")
        import shutil
        shutil.copy2(db_path, backup_path)
        
        # Intentar dump de la base de datos corrupta
        print("📤 Exportando datos...")
        try:
            corrupt_conn = sqlite3.connect(db_path)
            corrupt_conn.execute("PRAGMA integrity_check")  # Esto puede fallar
        except:
            pass
        
        # Crear nueva base de datos
        print("🆕 Creando nueva base de datos...")
        new_conn = sqlite3.connect(repaired_path)
        
        # Intentar copiar datos tabla por tabla
        corrupt_conn = sqlite3.connect(db_path)
        corrupt_cursor = corrupt_conn.cursor()
        
        # Obtener lista de tablas
        try:
            corrupt_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in corrupt_cursor.fetchall()]
            print(f"📋 Tablas encontradas: {len(tables)}")
            
            for table in tables:
                try:
                    print(f"  📤 Copiando tabla: {table}")
                    # Obtener schema
                    corrupt_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
                    schema = corrupt_cursor.fetchone()
                    if schema:
                        new_conn.execute(schema[0])
                    
                    # Copiar datos
                    corrupt_cursor.execute(f"SELECT * FROM {table}")
                    rows = corrupt_cursor.fetchall()
                    
                    if rows:
                        # Obtener columnas
                        corrupt_cursor.execute(f"PRAGMA table_info({table})")
                        columns = [col[1] for col in corrupt_cursor.fetchall()]
                        placeholders = ','.join(['?' for _ in columns])
                        column_names = ','.join(columns)
                        
                        new_cursor = new_conn.cursor()
                        new_cursor.executemany(
                            f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})",
                            rows
                        )
                        print(f"    ✅ {len(rows)} registros copiados")
                    else:
                        print(f"    ⚠️ Tabla vacía")
                        
                except Exception as e:
                    print(f"    ❌ Error copiando {table}: {e}")
                    continue
            
            new_conn.commit()
            corrupt_conn.close()
            new_conn.close()
            
            # Reemplazar archivo original
            print(f"\n🔄 Reemplazando base de datos original...")
            db_file.unlink()  # Eliminar corrupta
            Path(repaired_path).rename(db_path)  # Renombrar reparada
            
            print("✅ Base de datos reparada exitosamente")
            print(f"📦 Backup guardado en: {backup_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error durante la reparación: {e}")
            new_conn.close()
            if Path(repaired_path).exists():
                Path(repaired_path).unlink()
            return False
            
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal"""
    print("=" * 60)
    print("🔧 REPARACIÓN DE BASE DE DATOS SQLITE")
    print("=" * 60)
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else DB_PATH
    
    print(f"\n📁 Base de datos: {db_path}")
    print(f"📊 Tamaño: {Path(db_path).stat().st_size / 1024 / 1024:.2f} MB" if Path(db_path).exists() else "❌ No existe")
    
    response = input("\n¿Deseas continuar con la reparación? (s/n): ")
    if response.lower() != 's':
        print("❌ Operación cancelada")
        return
    
    success = repair_database(db_path)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Reparación completada")
        print("=" * 60)
        print("\n💡 Prueba ejecutar el bot nuevamente:")
        print("   python main.py")
    else:
        print("\n" + "=" * 60)
        print("❌ No se pudo reparar la base de datos")
        print("=" * 60)
        print("\n💡 Opciones:")
        print("   1. Descargar una copia fresca de producción")
        print("   2. Restaurar desde un backup anterior")
        print("   3. Crear una nueva base de datos vacía")


if __name__ == "__main__":
    main()

