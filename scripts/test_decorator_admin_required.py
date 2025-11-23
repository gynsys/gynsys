#!/usr/bin/env python3
"""
Script para probar si el decorador @admin_required permite acceso al superadmin
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SUPER_ADMIN_ID
from common.decorators import admin_required
from telegram import Update
from telegram.ext import ContextTypes

print("="*80)
print("PRUEBA: Decorador @admin_required para SuperAdmin")
print("="*80)

# Crear un update simulado para superadmin
class FakeUpdate:
    def __init__(self, user_id):
        self.effective_user = type('obj', (object,), {'id': user_id})()
        self.callback_query = type('obj', (object,), {
            'data': 'faqs_admin_hub',
            'answer': lambda *a, **k: None,
            'message': type('obj', (object,), {'message_id': 1})()
        })()

class FakeContext:
    pass

# Función de prueba con el decorador
@admin_required
async def test_function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"   ✅ Función ejecutada para usuario {update.effective_user.id}")
    return "SUCCESS"

async def test():
    print(f"\n1. Probando con SUPER_ADMIN_ID ({SUPER_ADMIN_ID})...")
    fake_update = FakeUpdate(SUPER_ADMIN_ID)
    fake_context = FakeContext()
    
    try:
        result = await test_function(fake_update, fake_context)
        print(f"   ✅ Decorador permitió acceso. Resultado: {result}")
    except Exception as e:
        print(f"   ❌ Decorador bloqueó acceso o hubo error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n2. Probando con usuario normal (123456789)...")
    fake_update2 = FakeUpdate(123456789)
    try:
        result = await test_function(fake_update2, fake_context)
        print(f"   ⚠️  Decorador permitió acceso (no debería). Resultado: {result}")
    except Exception as e:
        print(f"   ✅ Decorador bloqueó acceso correctamente: {type(e).__name__}")

asyncio.run(test())

print("\n" + "="*80)
print("PRUEBA COMPLETADA")
print("="*80)

