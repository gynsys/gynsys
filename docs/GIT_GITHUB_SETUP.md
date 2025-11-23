# 🚀 Guía: Conectar Proyecto a Git y GitHub con Despliegue Automático

## 📋 Pasos para Configurar Git y GitHub

### 1. Inicializar Repositorio Git Local

```powershell
# Navegar al directorio del proyecto
cd C:\Users\pablo\Desktop\gynsys

# Inicializar repositorio Git
git init

# Configurar usuario (si no está configurado globalmente)
git config user.name "Tu Nombre"
git config user.email "tu.email@ejemplo.com"
```

### 2. Verificar Archivos que se Van a Subir

```powershell
# Ver qué archivos se agregarán
git status

# Verificar que .env y archivos sensibles NO estén incluidos
git check-ignore .env
```

### 3. Crear Archivo .env.example (Opcional pero Recomendado)

Si no existe, crear un archivo `.env.example` con las variables necesarias (sin valores reales):

```powershell
# Crear archivo de ejemplo
@"
BOT_TOKEN=tu_token_aqui
SUPER_ADMIN_ID=tu_telegram_id
ENCRYPTION_KEY=tu_clave_de_encriptacion
DB_PATH=database/medical_bot.db
LOGS_SYS=True
"@ | Out-File -FilePath .env.example -Encoding utf8
```

### 4. Agregar Archivos al Repositorio

```powershell
# Agregar todos los archivos (respetando .gitignore)
git add .

# Verificar qué se agregó
git status

# Hacer commit inicial
git commit -m "Initial commit: Bot GynSys con migración a SQLAlchemy asíncrono"
```

### 5. Crear Repositorio en GitHub

1. Ve a [GitHub](https://github.com) e inicia sesión
2. Click en el botón **"+"** (arriba derecha) → **"New repository"**
3. Configuración:
   - **Repository name:** `gynsys-bot` (o el nombre que prefieras)
   - **Description:** "Bot de Telegram para gestión médica ginecológica"
   - **Visibility:** Private (recomendado para proyectos con datos sensibles)
   - **NO marques** "Initialize with README" (ya tenemos archivos)
4. Click en **"Create repository"**

### 6. Conectar Repositorio Local con GitHub

```powershell
# Agregar el repositorio remoto (reemplaza USERNAME y REPO_NAME)
git remote add origin https://github.com/USERNAME/REPO_NAME.git

# Verificar que se agregó correctamente
git remote -v

# Cambiar a rama main (si estás en master)
git branch -M main

# Subir código a GitHub
git push -u origin main
```

**Nota:** Si GitHub te pide autenticación, puedes usar:
- **Personal Access Token** (recomendado)
- O configurar SSH keys

### 7. Configurar Personal Access Token (Si es Necesario)

Si GitHub te pide autenticación:

1. Ve a GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click en **"Generate new token (classic)"**
3. Configura:
   - **Note:** "GynSys Bot Deployment"
   - **Expiration:** El tiempo que prefieras
   - **Scopes:** Marca `repo` (acceso completo a repositorios)
4. Click en **"Generate token"**
5. **Copia el token** (solo se muestra una vez)
6. Úsalo como contraseña cuando Git te pida credenciales

---

## 🔄 Configurar Despliegue Automático desde Servidor

### Opción 1: Usando GitHub Actions (Recomendado)

#### Crear Workflow de Despliegue

Crear archivo: `.github/workflows/deploy.yml`

```yaml
name: Deploy to Server

on:
  push:
    branches:
      - main
  workflow_dispatch:  # Permite ejecución manual

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /ruta/a/tu/proyecto
            git pull origin main
            source venv/bin/activate  # O la ruta a tu venv
            pip install -r requirements.txt
            # Reiniciar el bot (ajusta según tu sistema)
            sudo systemctl restart gynsys-bot  # Si usas systemd
            # O simplemente:
            # pkill -f "python main.py"
            # nohup python main.py > bot.log 2>&1 &
```

#### Configurar Secrets en GitHub

1. Ve a tu repositorio en GitHub
2. Settings → Secrets and variables → Actions
3. Click en **"New repository secret"**
4. Agregar estos secrets:
   - `SERVER_HOST`: IP o dominio de tu servidor
   - `SERVER_USER`: Usuario SSH del servidor
   - `SERVER_SSH_KEY`: Clave privada SSH para acceder al servidor

### Opción 2: Usando Webhook en el Servidor (Más Simple)

#### En el Servidor: Crear Script de Despliegue

```bash
#!/bin/bash
# /ruta/a/deploy.sh

cd /ruta/a/gynsys
git pull origin main
source venv/bin/activate
pip install -r requirements.txt

# Reiniciar el bot
pkill -f "python main.py"
nohup python main.py > bot.log 2>&1 &

echo "Despliegue completado"
```

#### Configurar Webhook en GitHub

1. Ve a tu repositorio → Settings → Webhooks
2. Click en **"Add webhook"**
3. Configuración:
   - **Payload URL:** `http://tu-servidor:puerto/webhook` (o usa un servicio como ngrok para desarrollo)
   - **Content type:** `application/json`
   - **Events:** Selecciona "Just the push event"
   - **Active:** ✓
4. Click en **"Add webhook"**

#### En el Servidor: Crear Endpoint Webhook (Python Flask)

```python
# webhook_server.py
from flask import Flask, request
import subprocess
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "tu_secreto_aqui"  # Configurar en GitHub webhook

@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Hub-Signature-256')
    if not signature:
        return 'No signature', 400
    
    # Verificar firma
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        request.data,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(f"sha256={expected_signature}", signature):
        return 'Invalid signature', 401
    
    # Ejecutar script de despliegue
    subprocess.run(['/ruta/a/deploy.sh'], check=True)
    return 'Deployment triggered', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Opción 3: Usando Git Hooks en el Servidor (Más Directo)

#### En el Servidor: Configurar Post-Receive Hook

```bash
# En el servidor, clonar el repositorio
cd /ruta/a/
git clone https://github.com/USERNAME/REPO_NAME.git gynsys

# Crear hook post-receive
cd gynsys/.git/hooks
cat > post-receive << 'EOF'
#!/bin/bash
cd /ruta/a/gynsys
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
pkill -f "python main.py"
nohup python main.py > bot.log 2>&1 &
EOF

chmod +x post-receive
```

---

## 📝 Comandos Git Útiles

### Trabajo Diario

```powershell
# Ver estado
git status

# Agregar cambios
git add .
# O archivos específicos
git add archivo.py

# Hacer commit
git commit -m "Descripción del cambio"

# Subir cambios
git push origin main

# Ver historial
git log --oneline

# Ver diferencias
git diff
```

### Ramas

```powershell
# Crear nueva rama
git checkout -b nombre-rama

# Cambiar de rama
git checkout main

# Fusionar rama
git merge nombre-rama

# Eliminar rama
git branch -d nombre-rama
```

---

## 🔒 Seguridad: Verificar que No se Suban Datos Sensibles

Antes de hacer push, verifica:

```powershell
# Verificar que .env está en .gitignore
git check-ignore .env

# Ver qué archivos se van a subir
git status

# Ver contenido de .gitignore
cat .gitignore

# Si accidentalmente agregaste .env, removerlo
git rm --cached .env
git commit -m "Remove .env from tracking"
```

---

## 🚨 Checklist Antes del Primer Push

- [ ] `.env` está en `.gitignore`
- [ ] Archivos de base de datos (`.db`) están en `.gitignore`
- [ ] `venv/` está en `.gitignore`
- [ ] Logs están en `.gitignore`
- [ ] No hay tokens o claves hardcodeadas en el código
- [ ] Se creó `.env.example` con variables de ejemplo
- [ ] Se hizo commit inicial
- [ ] Repositorio en GitHub está creado
- [ ] Remote origin está configurado

---

## 📚 Recursos Adicionales

- [Documentación de Git](https://git-scm.com/doc)
- [GitHub Docs](https://docs.github.com)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

---

**Nota:** Ajusta las rutas y configuraciones según tu entorno específico.

