"""
Archivo WSGI para PythonAnywhere

INSTRUCCIONES:
1. Copia este archivo al WSGI configuration file en PythonAnywhere
2. Reemplaza 'tu-usuario' con tu usuario real de PythonAnywhere
3. Asegúrate de que la ruta sea correcta (ej: /home/miusuario/gynsys)
4. IMPORTANTE: En la pestaña Web, configura el Virtualenv a: /home/tu-usuario/gynsys/venv
"""
import sys
import os

# ⚠️ IMPORTANTE: Reemplaza 'tu-usuario' con tu usuario real de PythonAnywhere
# Ejemplo: '/home/miusuario/gynsys'
path = '/home/tu-usuario/gynsys'
venv_path = os.path.join(path, 'venv')

# Agregar el directorio del proyecto al path
if path not in sys.path:
    sys.path.insert(0, path)

# Agregar el site-packages del entorno virtual al path
# Esto es necesario si PythonAnywhere no detecta automáticamente el venv
venv_site_packages = os.path.join(venv_path, 'lib', 'python3.10', 'site-packages')
if os.path.exists(venv_site_packages) and venv_site_packages not in sys.path:
    sys.path.insert(0, venv_site_packages)

# Cambiar al directorio del proyecto
os.chdir(path)

# Importar la aplicación Flask
from webhook_server import app

# Esta es la variable que PythonAnywhere busca
application = app

