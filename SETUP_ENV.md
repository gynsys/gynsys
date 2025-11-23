# Configuración de Variables de Entorno

Este documento explica cómo configurar las variables de entorno para el bot GynSys.

## 📋 Pasos para Configurar

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

O instalar solo python-dotenv:

```bash
pip install python-dotenv
```

### 2. Crear Archivo .env

Copia el archivo de ejemplo y completa con tus valores:

```bash
# En Windows (PowerShell)
Copy-Item .env.example .env

# En Linux/Mac
cp .env.example .env
```

### 3. Editar el Archivo .env

Abre el archivo `.env` con un editor de texto y completa los valores:

```env
# Token del bot de Telegram (obtener de @BotFather)
BOT_TOKEN=tu_token_aqui

# Tu Telegram ID (puedes obtenerlo de @userinfobot)
SUPER_ADMIN_ID=tu_telegram_id_aqui

# Clave de cifrado (generar una nueva con el comando abajo)
ENCRYPTION_KEY=tu_clave_de_cifrado_aqui
```

### 4. Generar Clave de Cifrado

Ejecuta este comando para generar una clave de cifrado segura:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode('utf-8'))"
```

Copia la clave generada y pégala en el archivo `.env` como valor de `ENCRYPTION_KEY`.

### 5. Verificar Configuración

Ejecuta el bot para verificar que todo está configurado correctamente:

```bash
python main.py
```

Si hay algún error sobre variables de entorno faltantes, verifica que el archivo `.env` existe y tiene todos los valores correctos.

## 🔒 Seguridad

- **NUNCA** commitees el archivo `.env` al repositorio
- El archivo `.env` ya está en `.gitignore` para prevenir commits accidentales
- En producción, considera usar variables de entorno del sistema en lugar del archivo `.env`

## 🌐 Variables de Entorno del Sistema (Alternativa)

Si prefieres usar variables de entorno del sistema en lugar del archivo `.env`:

### Windows (PowerShell)

```powershell
$env:BOT_TOKEN="tu_token_aqui"
$env:SUPER_ADMIN_ID="tu_telegram_id_aqui"
$env:ENCRYPTION_KEY="tu_clave_aqui"
```

### Linux/Mac

```bash
export BOT_TOKEN="tu_token_aqui"
export SUPER_ADMIN_ID="tu_telegram_id_aqui"
export ENCRYPTION_KEY="tu_clave_aqui"
```

## ✅ Verificación

Para verificar que las variables están cargadas correctamente, puedes ejecutar:

```python
from config import BOT_TOKEN, SUPER_ADMIN_ID, ENCRYPTION_KEY
print(f"BOT_TOKEN configurado: {'Sí' if BOT_TOKEN else 'No'}")
print(f"SUPER_ADMIN_ID: {SUPER_ADMIN_ID}")
print(f"ENCRYPTION_KEY configurado: {'Sí' if ENCRYPTION_KEY else 'No'}")
```

## 🆘 Solución de Problemas

### Error: "BOT_TOKEN no está configurado"

- Verifica que el archivo `.env` existe en la raíz del proyecto
- Verifica que `BOT_TOKEN` está escrito correctamente en el archivo `.env`
- Verifica que no hay espacios alrededor del signo `=`

### Error: "ModuleNotFoundError: No module named 'dotenv'"

```bash
pip install python-dotenv
```

### Error: "ENCRYPTION_KEY no está configurado"

- Genera una nueva clave con el comando proporcionado
- Asegúrate de copiarla completa en el archivo `.env`

