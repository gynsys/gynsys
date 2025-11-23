#!/bin/bash
# Script de despliegue automático para el servidor
# Uso: ./deploy.sh

set -e  # Salir si hay algún error

echo "🚀 Iniciando despliegue..."

# Cambiar al directorio del proyecto
cd "$(dirname "$0")"

# Actualizar código desde GitHub
echo "📥 Actualizando código desde GitHub..."
git pull origin main

# Activar entorno virtual (ajustar ruta según tu servidor)
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
else
    echo "⚠️  Entorno virtual no encontrado. Ajusta la ruta en el script."
fi

# Actualizar dependencias
echo "📦 Actualizando dependencias..."
pip install -r requirements.txt --quiet

# Reiniciar el bot
echo "🔄 Reiniciando el bot..."
pkill -f "python main.py" || true  # No fallar si el proceso no existe
sleep 2

# Iniciar el bot en segundo plano
echo "▶️  Iniciando bot..."
nohup python main.py > bot.log 2>&1 &

echo "✅ Despliegue completado"
echo "📋 Ver logs con: tail -f bot.log"

