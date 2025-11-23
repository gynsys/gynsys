#!/usr/bin/env python3
"""Script para verificar FAQs en la base de datos"""
import asyncio
import aiosqlite
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH

async def check_faqs():
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    
    print("=" * 60)
    print("📊 VERIFICACIÓN DE FAQs EN LA BASE DE DATOS")
    print("=" * 60)
    print()
    
    # Contar FAQs por bot_id
    cursor = await conn.execute('SELECT bot_id, COUNT(*) as count FROM faqs GROUP BY bot_id')
    rows = await cursor.fetchall()
    
    print("FAQs por bot_id:")
    for row in rows:
        print(f"  bot_id {row['bot_id']}: {row['count']} FAQs")
    
    print()
    
    # Obtener bot_id de MARI
    cursor = await conn.execute('''
        SELECT d.id, d.name, d.telegram_id, b.id as bot_id 
        FROM doctors d 
        LEFT JOIN bots b ON b.admin_user_id = d.telegram_id 
        WHERE d.name LIKE "%MARI%" OR d.name LIKE "%mari%"
    ''')
    mari_doctors = await cursor.fetchall()
    
    if mari_doctors:
        print("Doctores MARI encontrados:")
        for doc in mari_doctors:
            print(f"  ID: {doc['id']}, Nombre: {doc['name']}, Telegram ID: {doc['telegram_id']}, Bot ID: {doc['bot_id']}")
            
            if doc['bot_id']:
                # Contar FAQs de este bot_id
                cursor2 = await conn.execute('SELECT COUNT(*) as count FROM faqs WHERE bot_id = ?', (doc['bot_id'],))
                count_row = await cursor2.fetchone()
                print(f"    → FAQs actuales: {count_row['count']}")
                
                # Mostrar las FAQs
                cursor3 = await conn.execute('SELECT id, question, answer FROM faqs WHERE bot_id = ? ORDER BY display_order', (doc['bot_id'],))
                faqs = await cursor3.fetchall()
                if faqs:
                    print(f"    → Detalle de FAQs:")
                    for i, faq in enumerate(faqs, 1):
                        print(f"      {i}. ID: {faq['id']}, Pregunta: {faq['question'][:50]}...")
    else:
        print("No se encontraron doctores con nombre MARI")
    
    print()
    print("=" * 60)
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_faqs())

