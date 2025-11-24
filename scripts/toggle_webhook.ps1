# Script para activar/desactivar webhook fácilmente
# Uso: .\scripts\toggle_webhook.ps1 [on|off] [url]

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("on", "off", "status")]
    [string]$Action = "status",
    
    [Parameter(Mandatory=$false)]
    [string]$WebhookUrl = ""
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🔗 Gestión de Webhook del Bot" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "scripts\setup_webhook.py")) {
    Write-Host "❌ Error: No se encontró setup_webhook.py. Asegúrate de ejecutar este script desde la raíz del proyecto." -ForegroundColor Red
    exit 1
}

# Activar entorno virtual si existe
if (Test-Path "venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1" | Out-Null
}

switch ($Action) {
    "off" {
        Write-Host "🛑 Desactivando webhook (activando modo polling)..." -ForegroundColor Yellow
        python scripts\setup_webhook.py delete
        Write-Host ""
        Write-Host "✅ Webhook desactivado. Ahora puedes ejecutar el bot localmente con:" -ForegroundColor Green
        Write-Host "   python main.py" -ForegroundColor Gray
    }
    
    "on" {
        if ([string]::IsNullOrEmpty($WebhookUrl)) {
            Write-Host "❌ Error: Se requiere una URL para activar el webhook." -ForegroundColor Red
            Write-Host "   Uso: .\scripts\toggle_webhook.ps1 on https://tu-servidor.pythonanywhere.com/webhook" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "✅ Activando webhook para producción..." -ForegroundColor Yellow
        python scripts\setup_webhook.py set $WebhookUrl
        Write-Host ""
        Write-Host "✅ Webhook activado. El bot ahora funciona en modo webhook." -ForegroundColor Green
        Write-Host "⚠️  No puedes ejecutar el bot localmente con el mismo token ahora." -ForegroundColor Yellow
    }
    
    "status" {
        Write-Host "📊 Estado actual del webhook:" -ForegroundColor Cyan
        python scripts\setup_webhook.py info
    }
}

Write-Host ""

