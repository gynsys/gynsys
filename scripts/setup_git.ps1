# Script para configurar Git y preparar para GitHub
# Ejecutar: .\scripts\setup_git.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Configuración de Git para GynSys Bot" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si Git está instalado
try {
    $gitVersion = git --version
    Write-Host "✅ Git encontrado: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git no está instalado. Por favor, instálalo desde https://git-scm.com/" -ForegroundColor Red
    exit 1
}

# Verificar si ya es un repositorio Git
if (Test-Path .git) {
    Write-Host "⚠️  Ya existe un repositorio Git en este directorio." -ForegroundColor Yellow
    $continue = Read-Host "¿Deseas continuar de todos modos? (s/n)"
    if ($continue -ne "s") {
        exit 0
    }
} else {
    Write-Host "📦 Inicializando repositorio Git..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Repositorio Git inicializado" -ForegroundColor Green
}

# Verificar configuración de usuario
$userName = git config user.name
$userEmail = git config user.email

if (-not $userName -or -not $userEmail) {
    Write-Host ""
    Write-Host "⚠️  Git no tiene configurado usuario/email" -ForegroundColor Yellow
    $userName = Read-Host "Ingresa tu nombre para Git"
    $userEmail = Read-Host "Ingresa tu email para Git"
    git config user.name $userName
    git config user.email $userEmail
    Write-Host "✅ Usuario configurado" -ForegroundColor Green
} else {
    Write-Host "✅ Usuario Git: $userName ($userEmail)" -ForegroundColor Green
}

# Verificar .gitignore
if (Test-Path .gitignore) {
    Write-Host "✅ .gitignore encontrado" -ForegroundColor Green
    
    # Verificar que .env está ignorado
    $envIgnored = git check-ignore .env 2>$null
    if ($envIgnored) {
        Write-Host "✅ .env está correctamente ignorado" -ForegroundColor Green
    } else {
        Write-Host "⚠️  .env no está en .gitignore (pero debería estar)" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  .gitignore no encontrado" -ForegroundColor Yellow
}

# Verificar archivos sensibles
Write-Host ""
Write-Host "🔍 Verificando archivos sensibles..." -ForegroundColor Yellow

$sensitiveFiles = @(".env", "database\*.db", "*.log")
$foundSensitive = $false

foreach ($pattern in $sensitiveFiles) {
    $files = Get-ChildItem -Path . -Include $pattern -Recurse -ErrorAction SilentlyContinue
    if ($files) {
        foreach ($file in $files) {
            $ignored = git check-ignore $file.FullName 2>$null
            if (-not $ignored) {
                Write-Host "⚠️  Archivo sensible no ignorado: $($file.Name)" -ForegroundColor Yellow
                $foundSensitive = $true
            }
        }
    }
}

if (-not $foundSensitive) {
    Write-Host "✅ No se encontraron archivos sensibles sin ignorar" -ForegroundColor Green
}

# Ver estado actual
Write-Host ""
Write-Host "📊 Estado actual del repositorio:" -ForegroundColor Cyan
git status --short

# Preguntar si hacer commit inicial
Write-Host ""
$makeCommit = Read-Host "¿Deseas hacer commit inicial? (s/n)"
if ($makeCommit -eq "s") {
    Write-Host "📝 Agregando archivos..." -ForegroundColor Yellow
    git add .
    
    Write-Host "💾 Creando commit inicial..." -ForegroundColor Yellow
    $commitMessage = Read-Host "Mensaje del commit (Enter para usar mensaje por defecto)"
    if ([string]::IsNullOrWhiteSpace($commitMessage)) {
        $commitMessage = "Initial commit: Bot GynSys con migración a SQLAlchemy asíncrono"
    }
    
    git commit -m $commitMessage
    Write-Host "✅ Commit inicial creado" -ForegroundColor Green
}

# Información sobre GitHub
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Próximos pasos:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Crea un repositorio en GitHub:" -ForegroundColor Yellow
Write-Host "   - Ve a https://github.com/new" -ForegroundColor White
Write-Host "   - Crea un repositorio (preferiblemente Private)" -ForegroundColor White
Write-Host ""
Write-Host "2. Conecta el repositorio local con GitHub:" -ForegroundColor Yellow
Write-Host "   git remote add origin https://github.com/USERNAME/REPO_NAME.git" -ForegroundColor White
Write-Host ""
Write-Host "3. Sube el código:" -ForegroundColor Yellow
Write-Host "   git branch -M main" -ForegroundColor White
Write-Host "   git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "Ver documentacion completa en: docs/GIT_GITHUB_SETUP.md" -ForegroundColor Cyan
Write-Host ""

