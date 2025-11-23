# 🔐 Configurar Git en PythonAnywhere

## Problema: Git pide usuario/contraseña pero no funciona

GitHub ya no acepta contraseñas por HTTPS. Necesitas usar un **Personal Access Token** o configurar **SSH**.

---

## ✅ Solución 1: Personal Access Token (Rápida)

### Paso 1: Generar Token en GitHub

1. Ve a: https://github.com/settings/tokens
2. Click en **"Generate new token"** → **"Generate new token (classic)"**
3. Configura:
   - **Note:** `PythonAnywhere`
   - **Expiration:** Elige una duración (90 días, 1 año, etc.)
   - **Scopes:** Marca `repo` (acceso completo a repositorios)
4. Click **"Generate token"**
5. **⚠️ COPIA EL TOKEN INMEDIATAMENTE** (solo se muestra una vez)

### Paso 2: Usar el Token en PythonAnywhere

Cuando Git pida credenciales:
- **Username:** Tu usuario de GitHub
- **Password:** El token que acabas de generar (NO tu contraseña de GitHub)

### Paso 3: Guardar credenciales (opcional)

```bash
# Configurar Git para guardar credenciales
git config --global credential.helper store

# Ahora cuando hagas git pull, pedirá credenciales una vez
# y las guardará para futuras veces
git pull origin main
```

---

## ✅ Solución 2: SSH Keys (Más Segura)

### Paso 1: Generar SSH Key en PythonAnywhere

```bash
# Generar nueva SSH key
ssh-keygen -t ed25519 -C "pythonanywhere@gynsys"

# Presiona Enter para aceptar la ubicación por defecto
# Presiona Enter para dejar la passphrase vacía (o pon una si quieres)

# Ver la clave pública
cat ~/.ssh/id_ed25519.pub
```

### Paso 2: Agregar SSH Key a GitHub

1. Copia el contenido de `~/.ssh/id_ed25519.pub`
2. Ve a: https://github.com/settings/keys
3. Click **"New SSH key"**
4. **Title:** `PythonAnywhere`
5. **Key:** Pega la clave pública
6. Click **"Add SSH key"**

### Paso 3: Cambiar URL del repositorio a SSH

```bash
cd ~/gynsys

# Ver la URL actual
git remote -v

# Cambiar a SSH (reemplaza 'tu-usuario' con tu usuario de GitHub)
git remote set-url origin git@github.com:tu-usuario/gynsys.git

# Verificar
git remote -v

# Probar
git pull origin main
```

---

## ✅ Solución 3: Usar Token en la URL (Temporal)

```bash
cd ~/gynsys

# Reemplazar en la URL:
# https://github.com/usuario/repo.git
# Por:
# https://TOKEN@github.com/usuario/repo.git

git remote set-url origin https://TU_TOKEN@github.com/tu-usuario/gynsys.git

# Ahora puedes hacer git pull sin que pida credenciales
git pull origin main
```

**⚠️ Nota:** Esta opción guarda el token en texto plano. No es la más segura.

---

## 🔍 Verificar Configuración

```bash
# Ver URL del repositorio remoto
git remote -v

# Ver configuración de Git
git config --list
```

---

## 📝 Recomendación

- **Para empezar rápido:** Usa Solución 1 (Personal Access Token)
- **Para producción:** Usa Solución 2 (SSH Keys)

---

## ❓ Troubleshooting

### "Permission denied (publickey)"

- Verifica que la SSH key esté agregada a GitHub
- Prueba: `ssh -T git@github.com`

### "Authentication failed"

- Verifica que el token tenga permisos `repo`
- Genera un nuevo token si el anterior expiró

### "Repository not found"

- Verifica que tengas acceso al repositorio
- Verifica que la URL sea correcta

