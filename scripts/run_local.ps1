# Script para ejecutar el bot localmente en Windows (PowerShell)
# Uso: .\scripts\run_local.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 Iniciando Bot GynSys (Modo Local)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "main.py")) {
    Write-Host "❌ Error: No se encontró main.py. Asegúrate de ejecutar este script desde la raíz del proyecto." -ForegroundColor Red
    exit 1
}

# Verificar que existe el archivo .env
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Advertencia: No se encontró el archivo .env" -ForegroundColor Yellow
    Write-Host "   Creando archivo .env de ejemplo..." -ForegroundColor Yellow
    
    $envContent = @"
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
"@
    
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Archivo .env creado. Por favor, completa las variables necesarias." -ForegroundColor Green
    Write-Host ""
    exit 1
}

# Verificar que existe el entorno virtual
if (-not (Test-Path "venv")) {
    Write-Host "⚠️  No se encontró el entorno virtual. Creando..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error al crear el entorno virtual." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Entorno virtual creado." -ForegroundColor Green
}

# Activar entorno virtual
Write-Host "🔧 Activando entorno virtual..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Verificar que las dependencias están instaladas
Write-Host "📦 Verificando dependencias..." -ForegroundColor Yellow
$pipList = pip list
if ($pipList -notmatch "python-telegram-bot") {
    Write-Host "⚠️  Dependencias no encontradas. Instalando..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error al instalar dependencias." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Dependencias instaladas." -ForegroundColor Green
}

# Crear directorio de base de datos si no existe
if (-not (Test-Path "database")) {
    Write-Host "📁 Creando directorio de base de datos..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "database" | Out-Null
}

# Verificar variables de entorno críticas
Write-Host "🔍 Verificando configuración..." -ForegroundColor Yellow
$envFile = Get-Content ".env" -Raw
if ($envFile -notmatch "BOT_TOKEN=\S+") {
    Write-Host "❌ Error: BOT_TOKEN no está configurado en .env" -ForegroundColor Red
    exit 1
}
if ($envFile -notmatch "SUPER_ADMIN_ID=\d+") {
    Write-Host "❌ Error: SUPER_ADMIN_ID no está configurado en .env" -ForegroundColor Red
    exit 1
}
if ($envFile -notmatch "ENCRYPTION_KEY=\S+") {
    Write-Host "❌ Error: ENCRYPTION_KEY no está configurado en .env" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Configuración verificada." -ForegroundColor Green
Write-Host ""
Write-Host "🤖 Iniciando bot..." -ForegroundColor Cyan
Write-Host "   Presiona Ctrl+C para detener el bot" -ForegroundColor Gray
Write-Host ""

# Ejecutar el bot
python main.py

