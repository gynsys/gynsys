"""Script para ejecutar consultas SQL sobre el mensaje de bienvenida"""
import asyncio
import aiosqlite
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH

async def run_queries():
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    
    print("=" * 80)
    print("CONSULTAS SQL - MENSAJE DE BIENVENIDA")
    print("=" * 80)
    
    # Query 1: Ver mensaje completo para bot_id = 2
    print("\n" + "=" * 80)
    print("QUERY 1: Mensaje completo para bot_id = 2 (MARI)")
    print("=" * 80)
    cursor = await conn.execute("""
        SELECT bot_id, key, value, LENGTH(value) as longitud
        FROM text_content 
        WHERE key = 'msg_bienvenida_editable' AND bot_id = 2
    """)
    row = await cursor.fetchone()
    if row:
        print(f"\nBot ID: {row['bot_id']}")
        print(f"Key: {row['key']}")
        print(f"Longitud: {row['longitud']} caracteres")
        print(f"\nMensaje completo:")
        print("-" * 80)
        print(row['value'])
        print("-" * 80)
    else:
        print("\n❌ No se encontró mensaje para bot_id=2")
    
    # Query 2: Ver todos los mensajes de bienvenida
    print("\n\n" + "=" * 80)
    print("QUERY 2: Todos los mensajes de bienvenida")
    print("=" * 80)
    cursor2 = await conn.execute("""
        SELECT bot_id, LENGTH(value) as longitud, SUBSTR(value, 1, 80) as preview
        FROM text_content 
        WHERE key = 'msg_bienvenida_editable'
        ORDER BY bot_id
    """)
    rows2 = await cursor2.fetchall()
    if rows2:
        for r in rows2:
            print(f"\nBot ID: {r['bot_id']} | Longitud: {r['longitud']} chars")
            print(f"Preview: {r['preview']}...")
    else:
        print("\n❌ No se encontraron mensajes")
    
    # Query 3: Ver información de bots y sus mensajes
    print("\n\n" + "=" * 80)
    print("QUERY 3: Bots y sus mensajes de bienvenida")
    print("=" * 80)
    cursor3 = await conn.execute("""
        SELECT 
            b.id as bot_id,
            b.doctor_name,
            b.admin_user_id,
            CASE 
                WHEN tc.value IS NULL THEN '❌ Sin mensaje'
                ELSE '✅ Con mensaje (' || LENGTH(tc.value) || ' chars)'
            END as estado
        FROM bots b
        LEFT JOIN text_content tc ON tc.bot_id = b.id AND tc.key = 'msg_bienvenida_editable'
        WHERE b.is_active = 1
        ORDER BY b.id
    """)
    rows3 = await cursor3.fetchall()
    if rows3:
        print(f"\n{'Bot ID':<8} {'Doctor Name':<30} {'Admin User ID':<15} {'Estado'}")
        print("-" * 80)
        for r in rows3:
            print(f"{r['bot_id']:<8} {r['doctor_name']:<30} {r['admin_user_id']:<15} {r['estado']}")
    else:
        print("\n❌ No se encontraron bots")
    
    # Query 4: Verificar MARI específicamente
    print("\n\n" + "=" * 80)
    print("QUERY 4: Información de MARI (Doctor ID 279)")
    print("=" * 80)
    cursor4 = await conn.execute("""
        SELECT 
            d.id as doctor_id,
            d.name as doctor_name,
            d.telegram_id,
            b.id as bot_id,
            b.doctor_name as bot_name,
            CASE 
                WHEN tc.value IS NULL THEN '❌ Sin mensaje'
                ELSE '✅ Con mensaje'
            END as tiene_mensaje
        FROM doctors d
        LEFT JOIN bots b ON b.admin_user_id = d.telegram_id
        LEFT JOIN text_content tc ON tc.bot_id = b.id AND tc.key = 'msg_bienvenida_editable'
        WHERE d.id = 279 OR d.telegram_id = 5057356565
    """)
    rows4 = await cursor4.fetchall()
    if rows4:
        for r in rows4:
            print(f"\nDoctor ID: {r['doctor_id']}")
            print(f"Nombre: {r['doctor_name']}")
            print(f"Telegram ID: {r['telegram_id']}")
            print(f"Bot ID: {r['bot_id']}")
            print(f"Bot Name: {r['bot_name']}")
            print(f"Estado mensaje: {r['tiene_mensaje']}")
    else:
        print("\n❌ No se encontró información de MARI")
    
    await conn.close()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(run_queries())

