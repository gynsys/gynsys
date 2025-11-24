#!/bin/bash
# Script para activar/desactivar webhook fácilmente
# Uso: ./scripts/toggle_webhook.sh [on|off] [url]

ACTION=${1:-status}
WEBHOOK_URL=$2

echo "========================================"
echo "🔗 Gestión de Webhook del Bot"
echo "========================================"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "scripts/setup_webhook.py" ]; then
    echo "❌ Error: No se encontró setup_webhook.py. Asegúrate de ejecutar este script desde la raíz del proyecto."
    exit 1
fi

# Activar entorno virtual si existe
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

case $ACTION in
    off)
        echo "🛑 Desactivando webhook (activando modo polling)..."
        python scripts/setup_webhook.py delete
        echo ""
        echo "✅ Webhook desactivado. Ahora puedes ejecutar el bot localmente con:"
        echo "   python main.py"
        ;;
    on)
        if [ -z "$WEBHOOK_URL" ]; then
            echo "❌ Error: Se requiere una URL para activar el webhook."
            echo "   Uso: ./scripts/toggle_webhook.sh on https://tu-servidor.pythonanywhere.com/webhook"
            exit 1
        fi
        echo "✅ Activando webhook para producción..."
        python scripts/setup_webhook.py set "$WEBHOOK_URL"
        echo ""
        echo "✅ Webhook activado. El bot ahora funciona en modo webhook."
        echo "⚠️  No puedes ejecutar el bot localmente con el mismo token ahora."
        ;;
    status)
        echo "📊 Estado actual del webhook:"
        python scripts/setup_webhook.py info
        ;;
    *)
        echo "❌ Acción desconocida: $ACTION"
        echo "   Uso: ./scripts/toggle_webhook.sh [on|off|status] [url]"
        exit 1
        ;;
esac

echo ""

