# 🚀 Inicio Rápido - GynSys

## Paso 1: Preparar el Backend

### 1.1 Abrir terminal en el directorio backend
```powershell
cd C:\Users\pablo\Desktop\gynsys\backend
```

### 1.2 Activar entorno virtual (si existe)
```powershell
# Si tienes venv en el directorio raíz:
..\venv\Scripts\activate

# O crear uno nuevo:
python -m venv venv
venv\Scripts\activate
```

### 1.3 Instalar dependencias
```powershell
pip install -r requirements.txt
```

### 1.4 Crear la primera migración
```powershell
alembic revision --autogenerate -m "Initial migration - Doctors and Appointments"
alembic upgrade head
```

### 1.5 Iniciar el servidor
```powershell
uvicorn app.main:app --reload
```

✅ El backend estará en: **http://localhost:8000**
✅ Documentación API: **http://localhost:8000/docs**

---

## Paso 2: Preparar el Frontend

### 2.1 Abrir NUEVA terminal en el directorio frontend
```powershell
cd C:\Users\pablo\Desktop\gynsys\frontend
```

### 2.2 Instalar dependencias
```powershell
npm install
```

### 2.3 Crear archivo .env (si no existe)
Crear archivo `.env` en `frontend/` con:
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 2.4 Iniciar servidor de desarrollo
```powershell
npm run dev
```

✅ El frontend estará en: **http://localhost:5173**

---

## Paso 3: Probar el Sistema

### Prueba 1: Verificar que el backend funciona
1. Abrir navegador en: **http://localhost:8000/docs**
2. Deberías ver la documentación interactiva de Swagger
3. Probar el endpoint `GET /health` - debería retornar `{"status": "healthy"}`

### Prueba 2: Registro de Usuario
1. Ir a: **http://localhost:5173/register**
2. Completar formulario:
   - **Nombre Completo**: Dr. Juan Pérez
   - **Email**: juan@example.com
   - **Especialidad**: Ginecología (opcional)
   - **Contraseña**: password123
3. Click en "Registrarse"
4. ✅ Debería redirigir al dashboard automáticamente

### Prueba 3: Login
1. Si no estás logueado, ir a: **http://localhost:5173/login**
2. Ingresar:
   - **Email**: juan@example.com
   - **Contraseña**: password123
3. Click en "Iniciar sesión"
4. ✅ Debería redirigir al dashboard

### Prueba 4: Ver Perfil Público
1. Después de registrarte, tu slug será algo como: `dr-juan-perez`
2. Ir a: **http://localhost:5173/dr/dr-juan-perez**
3. ✅ Debería mostrar tu perfil público

### Prueba 5: API Directa (Swagger)
1. Ir a: **http://localhost:8000/docs**
2. Probar `POST /api/v1/auth/register`:
   ```json
   {
     "email": "maria@example.com",
     "password": "password123",
     "nombre_completo": "Dra. María García"
   }
   ```
3. Probar `POST /api/v1/auth/token`:
   - Click en "Authorize" (🔒)
   - Usar el token recibido
   - Probar `GET /api/v1/users/me`

---

## 🐛 Solución de Problemas Comunes

### Error: "ModuleNotFoundError"
**Solución**: Asegúrate de estar en el entorno virtual
```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

### Error: "Port 8000 already in use"
**Solución**: Cambiar puerto
```powershell
uvicorn app.main:app --reload --port 8001
```
Y actualizar `.env` del frontend con el nuevo puerto.

### Error: "CORS error" en el navegador
**Solución**: Verificar que `CORS_ORIGINS` en `backend/app/core/config.py` incluya `http://localhost:5173`

### Error: "Database locked"
**Solución**: Cerrar otras conexiones y reiniciar el servidor

### Error: "npm no se reconoce"
**Solución**: Instalar Node.js desde https://nodejs.org/

---

## ✅ Checklist de Verificación

- [ ] Backend inicia sin errores
- [ ] Puedo acceder a http://localhost:8000/docs
- [ ] Frontend inicia sin errores
- [ ] Puedo acceder a http://localhost:5173
- [ ] Puedo registrarme
- [ ] Puedo iniciar sesión
- [ ] Puedo ver mi perfil público
- [ ] El token JWT se guarda en localStorage (F12 → Application → Local Storage)

---

## 📝 Notas Importantes

1. **Base de datos**: Se creará automáticamente `gynsys.db` en el directorio `backend/`
2. **Secret Key**: Por defecto usa un valor inseguro. Cambiar en producción.
3. **Google OAuth**: Requiere configuración adicional (opcional para pruebas básicas)

---

## 🎯 Siguiente Paso

Una vez que todo funcione, puedes:
1. Personalizar el perfil desde el dashboard
2. Agregar más funcionalidades
3. Configurar Google OAuth (opcional)

