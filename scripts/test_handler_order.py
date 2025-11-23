#!/usr/bin/env python3
"""
Script para verificar el orden de los handlers y cuál se ejecuta primero
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram.ext import Application, CallbackQueryHandler
from config import BOT_TOKEN
from handlers.registration import register_all_handlers

print("="*80)
print("VERIFICACIÓN: Orden de handlers para faqs_admin_hub")
print("="*80)

app = Application.builder().token(BOT_TOKEN).build()
register_all_handlers(app)

# Obtener todos los handlers
handlers = app.handlers[0] if app.handlers else []

print(f"\nTotal de handlers registrados: {len(handlers)}")

# Buscar handlers relacionados con faqs_admin_hub
faqs_handlers = []
for i, handler in enumerate(handlers):
    if hasattr(handler, 'pattern') and handler.pattern:
        pattern_str = str(handler.pattern)
        if 'faqs_admin_hub' in pattern_str or 'faq' in pattern_str.lower():
            faqs_handlers.append((i, handler, pattern_str))

print(f"\nHandlers relacionados con FAQ (en orden de registro):")
for idx, handler, pattern in faqs_handlers:
    callback_name = "N/A"
    if hasattr(handler, 'callback'):
        callback_name = handler.callback.__name__ if hasattr(handler.callback, '__name__') else str(handler.callback)
    print(f"  [{idx}] {type(handler).__name__}")
    print(f"      Patrón: {pattern}")
    print(f"      Callback: {callback_name}")
    print()

# Buscar handle_all_callbacks
all_callbacks_handler = None
for i, handler in enumerate(handlers):
    if hasattr(handler, 'callback') and 'handle_all_callbacks' in str(handler.callback):
        all_callbacks_handler = (i, handler)
        break

if all_callbacks_handler:
    idx, handler = all_callbacks_handler
    print(f"\n⚠️  handle_all_callbacks está en la posición [{idx}]")
    print(f"   Esto significa que se ejecuta DESPUÉS de los handlers específicos")
    print(f"   Si hay un handler directo para 'faqs_admin_hub', se ejecutará PRIMERO")
else:
    print(f"\n❌ handle_all_callbacks NO encontrado")

# Verificar si hay handler directo
direct_handler = None
for idx, handler, pattern in faqs_handlers:
    if '^faqs_admin_hub$' in pattern:
        direct_handler = (idx, handler)
        break

if direct_handler:
    idx, handler = direct_handler
    print(f"\n✅ Handler directo encontrado en posición [{idx}]")
    print(f"   Este handler se ejecutará ANTES que handle_all_callbacks")
    print(f"   El callback debería llegar directamente a faqs_hub")
else:
    print(f"\n❌ NO hay handler directo para 'faqs_admin_hub'")
    print(f"   El callback debería llegar a handle_all_callbacks")

print("\n" + "="*80)
print("VERIFICACIÓN COMPLETADA")
print("="*80)

