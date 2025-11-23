"""
Script de revisión de código para detectar problemas comunes después de la refactorización.
Busca:
- Callbacks sin handlers
- Funciones async sin await
- Imports faltantes
- Patrones problemáticos
"""
import os
import re
from pathlib import Path
from collections import defaultdict

# Directorios a revisar
FEATURES_DIR = Path("features")
HANDLERS_DIR = Path("handlers")

# Resultados
callbacks_found = set()
handlers_found = set()
async_functions = []
potential_issues = []

def find_callbacks_in_file(file_path):
    """Encuentra todos los callback_data en un archivo"""
    callbacks = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Buscar callback_data="..."
            matches = re.findall(r'callback_data=["\']([^"\']+)["\']', content)
            callbacks.update(matches)
            # Buscar callback_data=f"..."
            matches = re.findall(r'callback_data=f["\']([^"\']+)["\']', content)
            callbacks.update(matches)
    except Exception as e:
        print(f"Error leyendo {file_path}: {e}")
    return callbacks

def find_handlers_in_file(file_path):
    """Encuentra todos los handlers registrados en un archivo"""
    handlers = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Buscar callback_data == "..."
            matches = re.findall(r'callback_data\s*==\s*["\']([^"\']+)["\']', content)
            handlers.update(matches)
            # Buscar pattern="^...$"
            matches = re.findall(r'pattern=["\']\^?([^$"\']+)\$?["\']', content)
            handlers.update(matches)
            # Buscar callback_data.startswith("...")
            matches = re.findall(r'callback_data\.startswith\(["\']([^"\']+)["\']', content)
            handlers.update(matches)
            # Buscar if callback_data == "..."
            matches = re.findall(r'if\s+callback_data\s*==\s*["\']([^"\']+)["\']', content)
            handlers.update(matches)
            # Buscar elif callback_data == "..."
            matches = re.findall(r'elif\s+callback_data\s*==\s*["\']([^"\']+)["\']', content)
            handlers.update(matches)
    except Exception as e:
        print(f"Error leyendo {file_path}: {e}")
    return handlers

def find_async_issues(file_path):
    """Encuentra funciones async que pueden tener problemas"""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            in_async_function = False
            function_name = None
            has_await = False
            
            for i, line in enumerate(lines, 1):
                # Detectar inicio de función async
                if re.match(r'\s*async\s+def\s+\w+', line):
                    in_async_function = True
                    function_name = re.search(r'async\s+def\s+(\w+)', line)
                    function_name = function_name.group(1) if function_name else "unknown"
                    has_await = False
                # Detectar await en la función
                elif in_async_function and 'await' in line:
                    has_await = True
                # Detectar fin de función (línea en blanco o nueva función)
                elif in_async_function and (line.strip() == '' or re.match(r'\s*def\s+\w+', line) or re.match(r'\s*async\s+def\s+\w+', line)):
                    if not has_await and function_name and 'test' not in function_name.lower():
                        # Verificar si llama a funciones async
                        func_content = ''.join(lines[max(0, i-20):i])
                        if re.search(r'\.(get_|add_|update_|delete_|create_|list_|find_)', func_content):
                            issues.append(f"{file_path}:{i} - Función async '{function_name}' puede necesitar await")
                    in_async_function = False
                    has_await = False
    except Exception as e:
        print(f"Error revisando {file_path}: {e}")
    return issues

def main():
    print("🔍 Iniciando revisión de código...\n")
    
    # 1. Buscar todos los callbacks
    print("📋 Buscando callbacks definidos...")
    for file_path in FEATURES_DIR.rglob("*.py"):
        callbacks = find_callbacks_in_file(file_path)
        callbacks_found.update(callbacks)
    
    print(f"   Encontrados {len(callbacks_found)} callbacks únicos")
    
    # 2. Buscar todos los handlers
    print("\n🔧 Buscando handlers registrados...")
    for file_path in HANDLERS_DIR.rglob("*.py"):
        handlers = find_handlers_in_file(file_path)
        handlers_found.update(handlers)
    
    for file_path in FEATURES_DIR.rglob("*.py"):
        handlers = find_handlers_in_file(file_path)
        handlers_found.update(handlers)
    
    print(f"   Encontrados {len(handlers_found)} handlers únicos")
    
    # 3. Comparar callbacks vs handlers
    print("\n⚠️  Callbacks sin handlers:")
    callbacks_without_handlers = []
    for callback in sorted(callbacks_found):
        # Ignorar callbacks dinámicos (con {})
        if '{' in callback or '$' in callback:
            continue
        # Buscar si hay un handler que coincida
        found = False
        for handler in handlers_found:
            # Coincidencia exacta
            if callback == handler:
                found = True
                break
            # Handler con patrón (empieza con)
            if handler.endswith('_') and callback.startswith(handler):
                found = True
                break
            # Handler con regex pattern
            if callback.startswith(handler.split('_')[0] + '_'):
                found = True
                break
        if not found:
            callbacks_without_handlers.append(callback)
    
    if callbacks_without_handlers:
        for callback in callbacks_without_handlers[:20]:  # Mostrar primeros 20
            print(f"   ❌ {callback}")
        if len(callbacks_without_handlers) > 20:
            print(f"   ... y {len(callbacks_without_handlers) - 20} más")
    else:
        print("   ✅ Todos los callbacks tienen handlers")
    
    # 4. Buscar problemas con async/await
    print("\n🔍 Buscando problemas con async/await...")
    for file_path in FEATURES_DIR.rglob("*.py"):
        issues = find_async_issues(file_path)
        potential_issues.extend(issues)
    
    if potential_issues:
        for issue in potential_issues[:10]:  # Mostrar primeros 10
            print(f"   ⚠️  {issue}")
        if len(potential_issues) > 10:
            print(f"   ... y {len(potential_issues) - 10} más")
    else:
        print("   ✅ No se encontraron problemas obvios con async/await")
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN:")
    print(f"   Callbacks encontrados: {len(callbacks_found)}")
    print(f"   Handlers encontrados: {len(handlers_found)}")
    print(f"   Callbacks sin handlers: {len(callbacks_without_handlers)}")
    print(f"   Problemas async/await: {len(potential_issues)}")
    print("="*60)

if __name__ == "__main__":
    main()

