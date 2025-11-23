#!/usr/bin/env python3
"""
Script de diagnóstico para investigar por qué el botón FAQ del panel admin del superadmin no funciona
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("="*80)
print("DIAGNÓSTICO: Botón FAQ desde Panel Admin del SuperAdmin")
print("="*80)

# 1. Verificar imports
print("\n1. VERIFICANDO IMPORTS...")
try:
    from config import SUPER_ADMIN_ID
    print(f"   ✅ SUPER_ADMIN_ID importado: {SUPER_ADMIN_ID}")
except Exception as e:
    print(f"   ❌ Error importando SUPER_ADMIN_ID: {e}")

try:
    from features.faqs.admin_handlers import faqs_hub, register as register_faqs_admin
    print(f"   ✅ faqs_hub importado correctamente")
    print(f"   ✅ register_faqs_admin importado correctamente")
except Exception as e:
    print(f"   ❌ Error importando faqs_hub: {e}")

try:
    from features.main_menu.admin_handler import handle_superadmin_callback
    print(f"   ✅ handle_superadmin_callback importado correctamente")
except Exception as e:
    print(f"   ❌ Error importando handle_superadmin_callback: {e}")

try:
    from handlers.callback_router import handle_all_callbacks
    print(f"   ✅ handle_all_callbacks importado correctamente")
except Exception as e:
    print(f"   ❌ Error importando handle_all_callbacks: {e}")

# 2. Verificar decoradores
print("\n2. VERIFICANDO DECORADORES...")
try:
    from common.decorators import admin_required
    print(f"   ✅ admin_required importado correctamente")
    
    # Verificar si el decorador permite superadmin
    import inspect
    source = inspect.getsource(admin_required)
    if "SUPER_ADMIN_ID" in source:
        print(f"   ✅ admin_required incluye verificación de SUPER_ADMIN_ID")
    else:
        print(f"   ⚠️  admin_required NO incluye verificación de SUPER_ADMIN_ID")
except Exception as e:
    print(f"   ❌ Error verificando decoradores: {e}")

# 3. Verificar callbacks registrados
print("\n3. VERIFICANDO REGISTRO DE HANDLERS...")
try:
    from handlers.registration import register_all_handlers
    from telegram.ext import Application
    from config import BOT_TOKEN
    
    # Crear aplicación temporal para verificar registros
    app = Application.builder().token(BOT_TOKEN).build()
    register_all_handlers(app)
    
    # Verificar si faqs_hub está registrado
    handlers = app.handlers[0] if app.handlers else []
    faqs_handlers = [h for h in handlers if hasattr(h, 'callback') and 'faq' in str(h.callback).lower()]
    print(f"   ✅ Handlers registrados: {len(handlers)} handlers totales")
    print(f"   ✅ Handlers relacionados con FAQ: {len(faqs_handlers)}")
    
    # Buscar específicamente el handler de faqs_admin_hub
    for handler in handlers:
        if hasattr(handler, 'pattern') and handler.pattern:
            pattern_str = str(handler.pattern)
            if 'faqs_admin_hub' in pattern_str or 'faq' in pattern_str.lower():
                print(f"   📋 Handler encontrado: {type(handler).__name__} con patrón: {pattern_str}")
except Exception as e:
    print(f"   ❌ Error verificando handlers: {e}")
    import traceback
    traceback.print_exc()

# 4. Verificar callback_data del botón
print("\n4. VERIFICANDO CALLBACK_DATA DEL BOTÓN...")
try:
    from features.main_menu.keyboards import get_doctors_management_keyboard
    import asyncio
    
    async def check_keyboard():
        keyboard = await get_doctors_management_keyboard()
        # Buscar el botón FAQ
        for row in keyboard.inline_keyboard:
            for button in row:
                if 'FAQ' in button.text or 'faq' in button.text.lower():
                    print(f"   ✅ Botón FAQ encontrado: '{button.text}' con callback: '{button.callback_data}'")
                    if button.callback_data == "faqs_admin_hub":
                        print(f"   ✅ Callback_data correcto: 'faqs_admin_hub'")
                    else:
                        print(f"   ⚠️  Callback_data incorrecto: '{button.callback_data}' (esperado: 'faqs_admin_hub')")
    
    asyncio.run(check_keyboard())
except Exception as e:
    print(f"   ❌ Error verificando keyboard: {e}")
    import traceback
    traceback.print_exc()

# 5. Verificar función handle_superadmin_callback
print("\n5. VERIFICANDO handle_superadmin_callback...")
try:
    import inspect
    source = inspect.getsource(handle_superadmin_callback)
    if "faqs_admin_hub" in source:
        print(f"   ✅ handle_superadmin_callback incluye manejo de 'faqs_admin_hub'")
        # Buscar la línea exacta
        lines = source.split('\n')
        for i, line in enumerate(lines, 1):
            if 'faqs_admin_hub' in line:
                print(f"   📋 Línea {i}: {line.strip()}")
    else:
        print(f"   ❌ handle_superadmin_callback NO incluye manejo de 'faqs_admin_hub'")
except Exception as e:
    print(f"   ❌ Error verificando handle_superadmin_callback: {e}")
    import traceback
    traceback.print_exc()

# 6. Verificar callback_router
print("\n6. VERIFICANDO callback_router...")
try:
    import inspect
    source = inspect.getsource(handle_all_callbacks)
    if "superadmin" in source.lower():
        print(f"   ✅ handle_all_callbacks incluye manejo de superadmin")
        # Buscar la línea donde se redirige
        lines = source.split('\n')
        for i, line in enumerate(lines, 1):
            if 'superadmin' in line.lower() and 'handle_superadmin' in line:
                print(f"   📋 Línea {i}: {line.strip()}")
    else:
        print(f"   ⚠️  handle_all_callbacks podría no estar manejando superadmin correctamente")
except Exception as e:
    print(f"   ❌ Error verificando callback_router: {e}")
    import traceback
    traceback.print_exc()

# 7. Verificar get_tenant_id para superadmin
print("\n7. VERIFICANDO get_tenant_id...")
try:
    from common.context_manager import get_tenant_id, SUPERADMIN_TENANT_ID
    print(f"   ✅ SUPERADMIN_TENANT_ID: {SUPERADMIN_TENANT_ID}")
    
    # Simular un update para superadmin
    class FakeUpdate:
        def __init__(self, user_id):
            self.effective_user = type('obj', (object,), {'id': user_id})()
    
    class FakeContext:
        pass
    
    async def test_tenant_id():
        fake_update = FakeUpdate(SUPER_ADMIN_ID)
        fake_context = FakeContext()
        bot_id = await get_tenant_id(fake_update, fake_context)
        print(f"   ✅ get_tenant_id para SUPER_ADMIN_ID ({SUPER_ADMIN_ID}): {bot_id}")
        if bot_id == SUPERADMIN_TENANT_ID:
            print(f"   ✅ Retorna el tenant_id correcto para superadmin")
        else:
            print(f"   ⚠️  Retorna {bot_id} pero se esperaba {SUPERADMIN_TENANT_ID}")
    
    asyncio.run(test_tenant_id())
except Exception as e:
    print(f"   ❌ Error verificando get_tenant_id: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("DIAGNÓSTICO COMPLETADO")
print("="*80)

