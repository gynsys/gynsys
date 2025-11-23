"""Script para verificar el mensaje de bienvenida en la BD"""
import asyncio
import aiosqlite
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH

async def check_welcome_in_db():
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    
    print("=" * 70)
    print("VERIFICACIÓN DE MENSAJE DE BIENVENIDA EN BASE DE DATOS")
    print("=" * 70)
    
    # Consulta 1: Verificar todos los mensajes de bienvenida
    print("\n1. TODOS LOS MENSAJES DE BIENVENIDA:")
    print("-" * 70)
    cursor = await conn.execute("""
        SELECT bot_id, key, LENGTH(value) as length, 
               SUBSTR(value, 1, 100) as preview
        FROM text_content 
        WHERE key = 'msg_bienvenida_editable'
        ORDER BY bot_id
    """)
    rows = await cursor.fetchall()
    
    if rows:
        for row in rows:
            print(f"\nBot ID: {row['bot_id']}")
            print(f"Longitud: {row['length']} caracteres")
            print(f"Preview: {row['preview']}...")
    else:
        print("\n❌ No se encontraron mensajes de bienvenida")
    
    # Consulta 2: Verificar específicamente bot_id=2
    print("\n\n2. MENSAJE ESPECÍFICO PARA BOT_ID = 2:")
    print("-" * 70)
    cursor2 = await conn.execute("""
        SELECT bot_id, key, value, LENGTH(value) as length
        FROM text_content 
        WHERE key = 'msg_bienvenida_editable' AND bot_id = 2
    """)
    row2 = await cursor2.fetchone()
    
    if row2:
        print(f"\n✅ Mensaje encontrado para bot_id=2")
        print(f"Longitud: {row2['length']} caracteres")
        print(f"\nValor completo:")
        print("-" * 70)
        print(row2['value'])
        print("-" * 70)
    else:
        print("\n❌ No se encontró mensaje para bot_id=2")
    
    # Consulta 3: Verificar todos los bot_id disponibles
    print("\n\n3. TODOS LOS BOT_ID EN LA TABLA:")
    print("-" * 70)
    cursor3 = await conn.execute("""
        SELECT DISTINCT bot_id 
        FROM text_content 
        ORDER BY bot_id
    """)
    bot_ids = await cursor3.fetchall()
    print(f"Bot IDs encontrados: {[r['bot_id'] for r in bot_ids]}")
    
    # Consulta 4: Verificar información de MARI
    print("\n\n4. INFORMACIÓN DE MARI (Doctor ID 279):")
    print("-" * 70)
    cursor4 = await conn.execute("""
        SELECT d.id as doctor_id, d.name, d.telegram_id, b.id as bot_id
        FROM doctors d
        LEFT JOIN bots b ON b.admin_user_id = d.telegram_id
        WHERE d.id = 279 OR d.telegram_id = 5057356565
    """)
    mari_info = await cursor4.fetchall()
    if mari_info:
        for r in mari_info:
            print(f"Doctor ID: {r['doctor_id']}")
            print(f"Nombre: {r['name']}")
            print(f"Telegram ID: {r['telegram_id']}")
            print(f"Bot ID: {r['bot_id']}")
    
    # Consulta 5: Verificar si hay múltiples entradas para bot_id=2
    print("\n\n5. VERIFICAR DUPLICADOS PARA BOT_ID=2:")
    print("-" * 70)
    cursor5 = await conn.execute("""
        SELECT COUNT(*) as count
        FROM text_content 
        WHERE key = 'msg_bienvenida_editable' AND bot_id = 2
    """)
    count_row = await cursor5.fetchone()
    print(f"Total de entradas para bot_id=2: {count_row['count']}")
    
    await conn.close()
    print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(check_welcome_in_db())

