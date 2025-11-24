import os
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
# Si el archivo .env no existe, se usarán las variables de entorno del sistema
load_dotenv()

# ============================================================================
# CONFIGURACIÓN DEL BOT
# ============================================================================
# Todas las variables sensibles se leen desde variables de entorno o archivo .env
# Ver .env.example para ver qué variables necesitas configurar

# Token del bot de Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN no está configurado. Por favor, configura la variable de entorno BOT_TOKEN o crea un archivo .env")

# ID del SuperAdmin (tu Telegram ID)
SUPER_ADMIN_ID = int(os.getenv('SUPER_ADMIN_ID', '0'))
if SUPER_ADMIN_ID == 0:
    raise ValueError("SUPER_ADMIN_ID no está configurado. Por favor, configura la variable de entorno SUPER_ADMIN_ID o crea un archivo .env")

# ============================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================================
DB_PATH = os.getenv('DB_PATH', 'database/medical_bot.db')
DATABASE_NAME = DB_PATH

# ============================================================================
# CONFIGURACIÓN DE CIFRADO
# ============================================================================
# IMPORTANTE: En producción, esta clave debe gestionarse de forma más segura:
# - Usar variables de entorno
# - Usar un gestor de secretos (ej: AWS Secrets Manager, HashiCorp Vault)
# - Nunca commitear la clave real en el repositorio
# 
# Para generar una nueva clave, ejecutar en Python:
# from cryptography.fernet import Fernet
# print(Fernet.generate_key().decode('utf-8'))
#
# NOTA: Si cambias esta clave, todos los datos cifrados existentes NO podrán ser descifrados.
# Asegúrate de hacer un backup antes de cambiar la clave.

ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', '')
if not ENCRYPTION_KEY:
    raise ValueError(
        "ENCRYPTION_KEY no está configurado. Por favor, configura la variable de entorno ENCRYPTION_KEY o crea un archivo .env.\n"
        "Para generar una clave: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode('utf-8'))\""
    )

# ============================================================================
# CONFIGURACIÓN GENERAL
# ============================================================================
LOGS_SYS = os.getenv('LOGS_SYS', 'True').lower() == 'true'

# Modo de ejecución: 'ON' para webhook, 'OFF' para polling
# Por defecto: OFF (polling para desarrollo local)
WEBHOOK = os.getenv('WEBHOOK', 'OFF').upper()
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')  # URL del webhook (solo necesario si WEBHOOK=ON)
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', '8443'))  # Puerto para webhook (solo necesario si WEBHOOK=ON)

# Estados para ConversationHandler
(MAIN_MENU, CITAS, GALERIA, FAQ, CONSEJOS, 
 UBICACIONES, CONTACTO, PRECIOS, ADMIN_PANEL) = range(9)