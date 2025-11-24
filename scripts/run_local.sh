#!/bin/bash
# Script para ejecutar el bot localmente en Linux/Mac
# Uso: ./scripts/run_local.sh

echo "========================================"
echo "🚀 Iniciando Bot GynSys (Modo Local)"
echo "========================================"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    echo "❌ Error: No se encontró main.py. Asegúrate de ejecutar este script desde la raíz del proyecto."
    exit 1
fi

# Verificar que existe el archivo .env
if [ ! -f ".env" ]; then
    echo "⚠️  Advertencia: No se encontró el archivo .env"
    echo "   Creando archivo .env de ejemplo..."
    
    cat > .env << EOF
# Token del bot de Telegram (obtener de @BotFather)
BOT_TOKEN=

# Tu Telegram ID (obtener de @userinfobot)
SUPER_ADMIN_ID=

# Ruta de la base de datos
DB_PATH=database/medical_bot.db

# Clave de cifrado (generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode('utf-8'))")
ENCRYPTION_KEY=

# Logs del sistema
LOGS_SYS=True
EOF
    
    echo "✅ Archivo .env creado. Por favor, completa las variables necesarias."
    echo ""
    exit 1
fi

# Verificar que existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "⚠️  No se encontró el entorno virtual. Creando..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Error al crear el entorno virtual."
        exit 1
    fi
    echo "✅ Entorno virtual creado."
fi

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Verificar que las dependencias están instaladas
echo "📦 Verificando dependencias..."
if ! pip list | grep -q "python-telegram-bot"; then
    echo "⚠️  Dependencias no encontradas. Instalando..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error al instalar dependencias."
        exit 1
    fi
    echo "✅ Dependencias instaladas."
fi

# Crear directorio de base de datos si no existe
if [ ! -d "database" ]; then
    echo "📁 Creando directorio de base de datos..."
    mkdir -p database
fi

# Verificar variables de entorno críticas
echo "🔍 Verificando configuración..."
if ! grep -q "BOT_TOKEN=.*[^[:space:]]" .env; then
    echo "❌ Error: BOT_TOKEN no está configurado en .env"
    exit 1
fi
if ! grep -q "SUPER_ADMIN_ID=[0-9]" .env; then
    echo "❌ Error: SUPER_ADMIN_ID no está configurado en .env"
    exit 1
fi
if ! grep -q "ENCRYPTION_KEY=.*[^[:space:]]" .env; then
    echo "❌ Error: ENCRYPTION_KEY no está configurado en .env"
    exit 1
fi

echo "✅ Configuración verificada."
echo ""
echo "🤖 Iniciando bot..."
echo "   Presiona Ctrl+C para detener el bot"
echo ""

# Ejecutar el bot
python main.py

