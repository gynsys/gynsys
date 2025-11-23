# Guía de Pruebas - GynSys

## 📋 Pasos para Probar el Sistema

### 1. Preparar el Backend

#### a) Crear archivo .env
```bash
cd backend
# Crear .env con las siguientes variables (o usar los valores por defecto)
```

#### b) Instalar dependencias
```bash
pip install -r requirements.txt
```

#### c) Crear migración inicial
```bash
alembic revision --autogenerate -m "Initial migration - Doctors and Appointments"
alembic upgrade head
```

#### d) Iniciar servidor
```bash
uvicorn app.main:app --reload
```

El servidor estará en: `http://localhost:8000`
Documentación API: `http://localhost:8000/docs`

### 2. Preparar el Frontend

#### a) Instalar dependencias
```bash
cd frontend
npm install
```

#### b) Crear archivo .env
```bash
# Crear .env con:
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

#### c) Iniciar servidor de desarrollo
```bash
npm run dev
```

El frontend estará en: `http://localhost:5173`

### 3. Probar el Sistema

#### Prueba 1: Registro de Usuario
1. Ir a `http://localhost:5173/register`
2. Completar formulario:
   - Nombre: "Dr. Juan Pérez"
   - Email: "juan@example.com"
   - Especialidad: "Ginecología" (opcional)
   - Contraseña: "password123" (mínimo 8 caracteres)
3. Click en "Registrarse"
4. ✅ Debería redirigir al dashboard

#### Prueba 2: Login
1. Cerrar sesión (si estás logueado)
2. Ir a `http://localhost:5173/login`
3. Ingresar:
   - Email: "juan@example.com"
   - Contraseña: "password123"
4. Click en "Iniciar sesión"
5. ✅ Debería redirigir al dashboard

#### Prueba 3: Ver Perfil Público
1. Después de registrarte, anota tu `slug_url` (ej: "dr-juan-perez")
2. Ir a `http://localhost:5173/dr/dr-juan-perez`
3. ✅ Debería mostrar tu perfil público con personalización

#### Prueba 4: API Directa (Swagger)
1. Ir a `http://localhost:8000/docs`
2. Probar endpoint `POST /api/v1/auth/register`
3. Probar endpoint `POST /api/v1/auth/token`
4. Probar endpoint `GET /api/v1/users/me` (requiere autenticación)

### 4. Verificar en Base de Datos

El archivo `gynsys.db` se creará en el directorio `backend/`

Puedes verificar los datos con:
```bash
sqlite3 backend/gynsys.db
.tables
SELECT * FROM doctors;
```

## 🐛 Solución de Problemas

### Error: "Module not found"
- Asegúrate de estar en el entorno virtual: `source venv/bin/activate` (Linux/Mac) o `venv\Scripts\activate` (Windows)

### Error: "Port already in use"
- Cambia el puerto en uvicorn: `uvicorn app.main:app --reload --port 8001`
- O mata el proceso que usa el puerto

### Error: "CORS error"
- Verifica que `CORS_ORIGINS` en backend incluya `http://localhost:5173`

### Error: "Database locked"
- Cierra otras conexiones a la base de datos
- Reinicia el servidor

## ✅ Checklist de Pruebas

- [ ] Backend inicia correctamente
- [ ] Frontend inicia correctamente
- [ ] Puedo registrarme
- [ ] Puedo iniciar sesión
- [ ] Puedo ver mi perfil público
- [ ] Puedo acceder al dashboard
- [ ] El token JWT se guarda en localStorage
- [ ] Las rutas protegidas funcionan
- [ ] El logout funciona

