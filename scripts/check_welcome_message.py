"""Script para verificar el mensaje de bienvenida en la BD"""
import asyncio
import aiosqlite
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH

async def check_welcome_message():
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    
    print("=" * 60)
    print("VERIFICACIÓN DE MENSAJES DE BIENVENIDA")
    print("=" * 60)
    
    # Verificar todos los mensajes de bienvenida
    cursor = await conn.execute("""
        SELECT bot_id, key, value, LENGTH(value) as length
        FROM text_content 
        WHERE key = 'msg_bienvenida_editable'
        ORDER BY bot_id
    """)
    rows = await cursor.fetchall()
    
    if rows:
        print(f"\n✅ Encontrados {len(rows)} mensajes de bienvenida:\n")
        for row in rows:
            print(f"Bot ID: {row['bot_id']}")
            print(f"Longitud: {row['length']} caracteres")
            print(f"Mensaje: {row['value'][:100]}...")
            print("-" * 60)
    else:
        print("\n❌ No se encontraron mensajes de bienvenida")
    
    # Verificar bot_id 2 específicamente
    print("\n" + "=" * 60)
    print("VERIFICACIÓN ESPECÍFICA PARA BOT_ID = 2")
    print("=" * 60)
    
    cursor2 = await conn.execute("""
        SELECT bot_id, key, value
        FROM text_content 
        WHERE key = 'msg_bienvenida_editable' AND bot_id = 2
    """)
    row2 = await cursor2.fetchone()
    
    if row2:
        print(f"\n✅ Mensaje encontrado para bot_id=2:")
        print(f"Valor completo:\n{row2['value']}")
    else:
        print("\n❌ No se encontró mensaje para bot_id=2")
    
    # Verificar qué bot_id tiene MARI
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE BOT_ID PARA MARI")
    print("=" * 60)
    
    cursor3 = await conn.execute("""
        SELECT d.id as doctor_id, d.name, d.telegram_id, b.id as bot_id
        FROM doctors d
        LEFT JOIN bots b ON b.admin_user_id = d.telegram_id
        WHERE d.name LIKE '%MARI%' OR d.name LIKE '%Mari%'
    """)
    rows3 = await cursor3.fetchall()
    
    if rows3:
        print(f"\n✅ Doctores encontrados:")
        for r in rows3:
            print(f"  Doctor: {r['name']} (ID: {r['doctor_id']}, Telegram: {r['telegram_id']})")
            print(f"  Bot ID: {r['bot_id']}")
    else:
        print("\n❌ No se encontró MARI")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_welcome_message())

