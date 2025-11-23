# Script rápido para hacer commit y push sin que se trabe
# Uso: .\scripts\quick_commit.ps1 "mensaje del commit"

param(
    [Parameter(Mandatory=$true)]
    [string]$Message
)

# Agregar todos los cambios
git add -A

# Commit con mensaje
git commit -m $Message

# Push
git push origin main

Write-Host "✅ Commit y push completados" -ForegroundColor Green

