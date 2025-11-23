#!/usr/bin/env python3
"""
Script para simular el flujo del callback faqs_admin_hub
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SUPER_ADMIN_ID
from utils.role_manager import RoleManager
from config import DB_PATH

print("="*80)
print("SIMULACIÓN: Flujo del callback faqs_admin_hub para SuperAdmin")
print("="*80)

role_manager = RoleManager(DB_PATH)

# Simular el flujo
async def test():
    user_id = SUPER_ADMIN_ID
    user_role = await role_manager.get_user_role(user_id)
    
    print(f"\n1. Usuario: {user_id}")
    print(f"   Rol detectado: {user_role}")
    
    # Simular callback_data
    callback_data = "faqs_admin_hub"
    print(f"\n2. Callback recibido: {callback_data}")
    
    # Verificar qué debería pasar según callback_router
    print(f"\n3. Según callback_router.py:")
    if user_role == 'superadmin':
        print(f"   ✅ Usuario es superadmin, debería redirigir a handle_superadmin_callback")
    else:
        print(f"   ❌ Usuario NO es superadmin (rol: {user_role})")
    
    # Verificar si handle_superadmin_callback maneja este callback
    print(f"\n4. Verificando handle_superadmin_callback...")
    try:
        from features.main_menu.admin_handler import admin_handler
        import inspect
        source = inspect.getsource(admin_handler.handle_superadmin_callback)
        
        if f'"{callback_data}"' in source or f"'{callback_data}'" in source:
            print(f"   ✅ handle_superadmin_callback SÍ maneja '{callback_data}'")
            # Buscar la línea exacta
            lines = source.split('\n')
            for i, line in enumerate(lines, 1):
                if callback_data in line:
                    print(f"   📋 Línea {i}: {line.strip()[:80]}")
        else:
            print(f"   ❌ handle_superadmin_callback NO maneja '{callback_data}'")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Verificar si hay un handler directo registrado
    print(f"\n5. Verificando handlers directos registrados...")
    try:
        from telegram.ext import Application
        from config import BOT_TOKEN
        from handlers.registration import register_all_handlers
        
        app = Application.builder().token(BOT_TOKEN).build()
        register_all_handlers(app)
        
        # Buscar handlers que manejen faqs_admin_hub directamente
        handlers = app.handlers[0] if app.handlers else []
        direct_handlers = []
        for handler in handlers:
            if hasattr(handler, 'pattern') and handler.pattern:
                pattern_str = str(handler.pattern)
                if 'faqs_admin_hub' in pattern_str:
                    direct_handlers.append(handler)
                    print(f"   📋 Handler directo encontrado: {type(handler).__name__}")
                    print(f"      Patrón: {pattern_str}")
                    if hasattr(handler, 'callback'):
                        print(f"      Callback: {handler.callback}")
        
        if direct_handlers:
            print(f"   ⚠️  Hay {len(direct_handlers)} handler(s) directo(s) que podrían interceptar el callback")
            print(f"   ⚠️  Estos handlers se ejecutan ANTES de handle_all_callbacks")
        else:
            print(f"   ✅ No hay handlers directos, el callback debería llegar a handle_all_callbacks")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

# Ejecutar el test
asyncio.run(test())

print(f"\n1. Usuario: {user_id}")
print(f"   Rol detectado: {user_role}")

# Simular callback_data
callback_data = "faqs_admin_hub"
print(f"\n2. Callback recibido: {callback_data}")

# Verificar qué debería pasar según callback_router
print(f"\n3. Según callback_router.py:")
if user_role == 'superadmin':
    print(f"   ✅ Usuario es superadmin, debería redirigir a handle_superadmin_callback")
else:
    print(f"   ❌ Usuario NO es superadmin (rol: {user_role})")

# Verificar si handle_superadmin_callback maneja este callback
print(f"\n4. Verificando handle_superadmin_callback...")
try:
    from features.main_menu.admin_handler import admin_handler
    import inspect
    source = inspect.getsource(admin_handler.handle_superadmin_callback)
    
    if f'"{callback_data}"' in source or f"'{callback_data}'" in source:
        print(f"   ✅ handle_superadmin_callback SÍ maneja '{callback_data}'")
        # Buscar la línea exacta
        lines = source.split('\n')
        for i, line in enumerate(lines, 1):
            if callback_data in line:
                print(f"   📋 Línea {i}: {line.strip()[:80]}")
    else:
        print(f"   ❌ handle_superadmin_callback NO maneja '{callback_data}'")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Verificar si hay un handler directo registrado
print(f"\n5. Verificando handlers directos registrados...")
try:
    from telegram.ext import Application
    from config import BOT_TOKEN
    from handlers.registration import register_all_handlers
    
    app = Application.builder().token(BOT_TOKEN).build()
    register_all_handlers(app)
    
    # Buscar handlers que manejen faqs_admin_hub directamente
    handlers = app.handlers[0] if app.handlers else []
    direct_handlers = []
    for handler in handlers:
        if hasattr(handler, 'pattern') and handler.pattern:
            pattern_str = str(handler.pattern)
            if 'faqs_admin_hub' in pattern_str:
                direct_handlers.append(handler)
                print(f"   📋 Handler directo encontrado: {type(handler).__name__}")
                print(f"      Patrón: {pattern_str}")
                if hasattr(handler, 'callback'):
                    print(f"      Callback: {handler.callback}")
    
    if direct_handlers:
        print(f"   ⚠️  Hay {len(direct_handlers)} handler(s) directo(s) que podrían interceptar el callback")
        print(f"   ⚠️  Estos handlers se ejecutan ANTES de handle_all_callbacks")
    else:
        print(f"   ✅ No hay handlers directos, el callback debería llegar a handle_all_callbacks")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("SIMULACIÓN COMPLETADA")
print("="*80)

