"""Script para verificar el estado del módulo quiz"""
import asyncio
import aiosqlite
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH

async def check_quiz_module():
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    
    print("=" * 50)
    print("VERIFICACIÓN DEL MÓDULO QUIZ")
    print("=" * 50)
    
    # Verificar módulos activos
    cursor = await conn.execute("""
        SELECT em.doctor_id, em.module_name, em.is_active, d.name as doctor_name
        FROM extra_modules em
        JOIN doctors d ON em.doctor_id = d.id
        WHERE em.module_name = 'quiz'
    """)
    rows = await cursor.fetchall()
    
    if rows:
        print("\n✅ Módulo quiz encontrado en la base de datos:")
        for row in rows:
            status = "ACTIVO" if row['is_active'] == 1 else "INACTIVO"
            print(f"  - Doctor: {row['doctor_name']} (ID: {row['doctor_id']}) - {status}")
    else:
        print("\n❌ No se encontró el módulo quiz en la base de datos")
    
    # Verificar todos los módulos disponibles
    cursor2 = await conn.execute("""
        SELECT DISTINCT module_name FROM extra_modules
    """)
    all_modules = await cursor2.fetchall()
    print(f"\n📦 Módulos registrados en total: {len(all_modules)}")
    for mod in all_modules:
        print(f"  - {mod['module_name']}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_quiz_module())

