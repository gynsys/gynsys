"""
Archivo WSGI para PythonAnywhere

INSTRUCCIONES:
1. Copia este archivo al WSGI configuration file en PythonAnywhere
2. Reemplaza 'tu-usuario' con tu usuario real de PythonAnywhere
3. Asegúrate de que la ruta sea correcta (ej: /home/miusuario/gynsys)
"""
import sys
import os

# ⚠️ IMPORTANTE: Reemplaza 'tu-usuario' con tu usuario real de PythonAnywhere
# Ejemplo: '/home/miusuario/gynsys'
path = '/home/tu-usuario/gynsys'

if path not in sys.path:
    sys.path.insert(0, path)

# Cambiar al directorio del proyecto
os.chdir(path)

# Importar la aplicación Flask
from webhook_server import app

# Esta es la variable que PythonAnywhere busca
application = app

