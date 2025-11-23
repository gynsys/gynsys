#!/usr/bin/env python3
"""
Script de auditoría para identificar archivos y funciones huérfanas (no utilizadas).

Este script busca:
1. Archivos Python que no se importan en ningún lugar
2. Funciones que no se llaman
3. Módulos que no se usan

Ejecutar: python scripts/audit_orphans.py
"""

import os
import ast
import re
from pathlib import Path
from collections import defaultdict

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.parent

# Archivos y directorios a ignorar
IGNORE_PATTERNS = [
    '__pycache__',
    'venv',
    '.git',
    '__init__.py',
    'main.py',
    'config.py',
    'backup.py',
    'scripts',
    '.env',
    '.env.example',
    'requirements.txt',
    '*.md',
    '*.log',
    '*.db',
    '*.db-shm',
    '*.db-wal',
    '*.sqbpro',
    '*.png',
    '*.jpg',
    '*.json',
]

# Archivos que sabemos que se usan (registrados en handlers)
KNOWN_USED_FILES = {
    'handlers/registration.py',
    'handlers/start_handler.py',
    'handlers/callback_router.py',
    'handlers/inactive_doctor_handler.py',
    'utils/startup.py',
    'utils/encryption.py',
    'utils/role_manager.py',
    'database/connection.py',
    'database/sql_utils.py',
}

def should_ignore_file(file_path: Path) -> bool:
    """Verifica si un archivo debe ser ignorado."""
    file_str = str(file_path)
    for pattern in IGNORE_PATTERNS:
        if pattern in file_str:
            return True
    return False

def get_all_python_files():
    """Obtiene todos los archivos Python del proyecto."""
    python_files = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Ignorar directorios
        dirs[:] = [d for d in dirs if not should_ignore_file(Path(root) / d)]
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                if not should_ignore_file(file_path):
                    python_files.append(file_path)
    
    return python_files

def extract_imports(file_path: Path):
    """Extrae todos los imports de un archivo Python."""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
    except Exception as e:
        print(f"⚠️  Error al analizar {file_path}: {e}")
    
    return imports

def get_module_name(file_path: Path) -> str:
    """Convierte una ruta de archivo a nombre de módulo."""
    relative = file_path.relative_to(PROJECT_ROOT)
    parts = relative.parts[:-1] + (relative.stem,)
    return '.'.join(parts).replace('\\', '/').replace('/', '.')

def find_orphan_files():
    """Encuentra archivos que no se importan en ningún lugar."""
    print("🔍 Analizando archivos del proyecto...")
    
    all_files = get_all_python_files()
    all_imports = set()
    file_modules = {}
    
    # Primero, extraer todos los imports
    for file_path in all_files:
        imports = extract_imports(file_path)
        all_imports.update(imports)
        module_name = get_module_name(file_path)
        file_modules[module_name] = file_path
    
    # Agregar módulos conocidos como usados
    for known_file in KNOWN_USED_FILES:
        module_name = known_file.replace('/', '.').replace('\\', '.').replace('.py', '')
        all_imports.add(module_name)
    
    # Buscar archivos huérfanos
    orphan_files = []
    for module_name, file_path in file_modules.items():
        # Verificar si el módulo se importa en algún lugar
        is_imported = False
        
        # Verificar importaciones directas
        for imp in all_imports:
            if module_name.startswith(imp) or imp.startswith(module_name.split('.')[0]):
                is_imported = True
                break
        
        # Verificar si es parte de un paquete que se importa
        module_parts = module_name.split('.')
        for i in range(len(module_parts)):
            partial_module = '.'.join(module_parts[:i+1])
            if partial_module in all_imports:
                is_imported = True
                break
        
        if not is_imported:
            orphan_files.append((file_path, module_name))
    
    return orphan_files

def find_orphan_functions():
    """Encuentra funciones que no se llaman en ningún lugar."""
    print("🔍 Analizando funciones...")
    
    all_files = get_all_python_files()
    all_function_calls = set()
    defined_functions = defaultdict(list)
    
    # Extraer todas las llamadas a funciones
    for file_path in all_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
                
                # Buscar llamadas a funciones
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            all_function_calls.add(node.func.id)
                        elif isinstance(node.func, ast.Attribute):
                            all_function_calls.add(node.func.attr)
                
                # Buscar definiciones de funciones
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        defined_functions[file_path].append(node.name)
        except Exception as e:
            print(f"⚠️  Error al analizar {file_path}: {e}")
    
    # Encontrar funciones definidas pero no llamadas
    orphan_functions = []
    for file_path, functions in defined_functions.items():
        for func_name in functions:
            # Ignorar funciones especiales (__init__, main, etc.)
            if func_name.startswith('__') or func_name == 'main':
                continue
            
            # Verificar si se llama en algún lugar
            if func_name not in all_function_calls:
                # Verificar si se exporta o registra de alguna manera
                is_exported = False
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Buscar patrones de exportación/registro
                        if f'register' in content or f'export' in content:
                            # Verificar si la función está en un patrón de registro
                            if re.search(rf'register.*{func_name}|{func_name}.*register', content):
                                is_exported = True
                except:
                    pass
                
                if not is_exported:
                    orphan_functions.append((file_path, func_name))
    
    return orphan_functions

def main():
    """Función principal de auditoría."""
    print("=" * 70)
    print("📊 AUDITORÍA DE ARCHIVOS Y FUNCIONES HUÉRFANAS")
    print("=" * 70)
    print()
    
    # 1. Buscar archivos huérfanos
    print("1️⃣  Buscando archivos no importados...")
    orphan_files = find_orphan_files()
    
    print(f"\n📁 Archivos potencialmente huérfanos encontrados: {len(orphan_files)}")
    if orphan_files:
        print("\n⚠️  ARCHIVOS QUE NO SE IMPORTAN DIRECTAMENTE:")
        for file_path, module_name in sorted(orphan_files):
            rel_path = file_path.relative_to(PROJECT_ROOT)
            print(f"   - {rel_path} (módulo: {module_name})")
    else:
        print("   ✅ No se encontraron archivos huérfanos obvios")
    
    print()
    
    # 2. Buscar funciones huérfanas
    print("2️⃣  Buscando funciones no utilizadas...")
    orphan_functions = find_orphan_functions()
    
    print(f"\n🔧 Funciones potencialmente huérfanas encontradas: {len(orphan_functions)}")
    if orphan_functions:
        print("\n⚠️  FUNCIONES QUE NO SE LLAMAN:")
        current_file = None
        for file_path, func_name in sorted(orphan_functions):
            rel_path = file_path.relative_to(PROJECT_ROOT)
            if rel_path != current_file:
                print(f"\n   📄 {rel_path}:")
                current_file = rel_path
            print(f"      - {func_name}()")
    else:
        print("   ✅ No se encontraron funciones huérfanas obvias")
    
    print()
    print("=" * 70)
    print("📝 NOTAS:")
    print("   - Algunos archivos pueden ser usados dinámicamente (registros, callbacks)")
    print("   - Revisa manualmente antes de eliminar cualquier archivo")
    print("   - Los archivos en 'scripts/' son utilitarios y pueden no importarse")
    print("=" * 70)

if __name__ == "__main__":
    main()

