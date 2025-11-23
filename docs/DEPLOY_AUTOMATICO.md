# 🚀 Configuración de Despliegue Automático

## ✅ Estado Actual
- ✅ Repositorio en GitHub: `https://github.com/gynsys/gynsys.git`
- ✅ Código subido a la rama `main`
- ⏳ Pendiente: Configurar despliegue automático

---

## Opción 1: Script de Despliegue Simple (Recomendado para empezar)

### En el Servidor: Crear Script de Despliegue

```bash
#!/bin/bash
# /ruta/a/gynsys/deploy.sh

cd /ruta/a/gynsys
git pull origin main

# Activar entorno virtual
source venv/bin/activate  # O la ruta a tu venv

# Actualizar dependencias
pip install -r requirements.txt

# Reiniciar el bot
pkill -f "python main.py"
nohup python main.py > bot.log 2>&1 &

echo "✅ Despliegue completado"
```

**Hacer ejecutable:**
```bash
chmod +x deploy.sh
```

**Ejecutar manualmente cuando necesites:**
```bash
./deploy.sh
```

---

## Opción 2: GitHub Actions (Despliegue Automático)

### Crear Workflow de Despliegue

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
            cd /ruta/a/gynsys
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            pkill -f "python main.py"
            nohup python main.py > bot.log 2>&1 &
```

### Configurar Secrets en GitHub

1. Ve a: `https://github.com/gynsys/gynsys/settings/secrets/actions`
2. Click en **"New repository secret"**
3. Agregar estos secrets:
   - `SERVER_HOST`: IP o dominio de tu servidor
   - `SERVER_USER`: Usuario SSH (ej: `root` o `ubuntu`)
   - `SERVER_SSH_KEY`: Clave privada SSH para acceder al servidor

**Generar clave SSH (si no tienes):**
```bash
ssh-keygen -t ed25519 -C "github-actions"
# Copiar la clave privada (~/.ssh/id_ed25519) a GitHub Secrets
# Agregar la clave pública (~/.ssh/id_ed25519.pub) al servidor:
ssh-copy-id usuario@servidor
```

---

## Opción 3: Webhook en el Servidor

### En el Servidor: Crear Endpoint Webhook

```python
# webhook_server.py
from flask import Flask, request
import subprocess
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "tu_secreto_aqui"  # Configurar en GitHub

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
    subprocess.run(['/ruta/a/gynsys/deploy.sh'], check=True)
    return 'Deployment triggered', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Configurar Webhook en GitHub

1. Ve a: `https://github.com/gynsys/gynsys/settings/webhooks`
2. Click en **"Add webhook"**
3. Configuración:
   - **Payload URL:** `http://tu-servidor:5000/webhook`
   - **Content type:** `application/json`
   - **Secret:** El mismo que usaste en `WEBHOOK_SECRET`
   - **Events:** "Just the push event"
4. Click en **"Add webhook"**

---

## Opción 4: Cron Job (Despliegue Programado)

### En el Servidor: Configurar Cron

```bash
# Editar crontab
crontab -e

# Agregar línea para verificar cambios cada 5 minutos
*/5 * * * * cd /ruta/a/gynsys && git fetch && [ $(git rev-parse HEAD) != $(git rev-parse origin/main) ] && git pull origin main && source venv/bin/activate && pip install -r requirements.txt && pkill -f "python main.py" && nohup python main.py > bot.log 2>&1 &
```

---

## Recomendación

Para empezar, usa la **Opción 1 (Script Simple)**:
- Es la más fácil de configurar
- No requiere configuración adicional
- Puedes ejecutarlo manualmente cuando necesites

Luego, cuando quieras automatizar, puedes migrar a **Opción 2 (GitHub Actions)**.

---

## Verificación

Después de configurar el despliegue:

1. **Hacer un cambio pequeño** en el código
2. **Hacer commit y push:**
   ```powershell
   git add .
   git commit -m "Test deployment"
   git push origin main
   ```
3. **Verificar** que el servidor se actualiza automáticamente

---

## Troubleshooting

### El bot no se reinicia
- Verificar que el proceso se llama correctamente: `ps aux | grep python`
- Usar `pkill -9 -f "python main.py"` para forzar

### Permisos denegados
- Verificar permisos del script: `chmod +x deploy.sh`
- Verificar permisos del directorio: `chmod 755 /ruta/a/gynsys`

### Git pull falla
- Verificar que el servidor tiene acceso al repositorio
- Configurar SSH keys o usar HTTPS con token

---

**¿Necesitas ayuda con alguna opción específica?**

