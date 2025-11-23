# Migración a SQLAlchemy Asíncrono - Fase 1 Completada ✅

## 📋 Resumen

Se ha completado la **Fase 1** de la migración a SQLAlchemy asíncrono. La estructura base está lista y lista para usar.

## 🏗️ Estructura Creada

```
database/
├── engine.py                      # ✅ Configuración del engine asíncrono
├── session.py                     # ✅ Session factory y context managers
├── __init__.py                    # ✅ Exporta componentes principales
│
├── models/                         # ✅ Modelos SQLAlchemy organizados
│   ├── __init__.py                # ✅ Exporta todos los modelos
│   ├── base.py                    # ✅ Base declarativa y mixins
│   ├── user.py                    # ✅ Doctor, PatientDoctor
│   ├── bot.py                     # ✅ Bot, UserTenant
│   ├── medical.py                 # ✅ MedicalHistory
│   ├── appointment.py             # ✅ Slot, Appointment
│   ├── content.py                 # ✅ TextContent, FAQ, Gallery, Precio
│   ├── location.py                # ✅ Location
│   ├── pdf.py                     # ✅ PDFSetting
│   └── extra.py                    # ✅ ExtraModule, TestQuestion
│
└── repositories/                  # ✅ CAPA DE ACCESO A DATOS
    ├── __init__.py
    └── base_repository.py         # ✅ Repository base con CRUD común
```

## 📦 Dependencias Agregadas

Se actualizó `requirements.txt` con:
- `sqlalchemy[asyncio]>=2.0.0`
- `alembic>=1.12.0`

## 🔧 Instalación

```bash
pip install -r requirements.txt
```

## 🚀 Uso Básico

### 1. Inicializar Engine

El engine se inicializa automáticamente en `main.py`:

```python
from database.engine import init_engine, close_engine

await init_engine()
# ... usar base de datos ...
await close_engine()
```

### 2. Obtener Sesión

```python
from database.session import get_session
from database.models import Doctor

async with get_session() as session:
    # Hacer queries aquí
    result = await session.execute(select(Doctor))
    doctors = result.scalars().all()
    # Session se cierra automáticamente y hace commit
```

### 3. Usar Repository Base

```python
from database.repositories import BaseRepository
from database.models import Doctor
from database.session import get_session

async with get_session() as session:
    repo = BaseRepository(Doctor, session)
    
    # Crear
    doctor = await repo.create(name="Dr. Test", telegram_id=123456)
    
    # Obtener por ID
    doctor = await repo.get_by_id(1)
    
    # Actualizar
    await repo.update(1, name="Dr. Updated")
    
    # Eliminar
    await repo.delete(1)
    
    # Filtrar
    doctors = await repo.filter_by(is_active=True)
```

## 📝 Modelos Disponibles

Todos los modelos están disponibles en `database.models`:

- `Doctor` - Doctores del sistema
- `PatientDoctor` - Asociación paciente-médico
- `Bot` - Bots/tenants
- `UserTenant` - Asociación usuario-tenant
- `MedicalHistory` - Historiales médicos
- `Slot` - Cupos de citas
- `Appointment` - Citas reservadas
- `TextContent` - Contenido de texto configurable
- `FAQ` - Preguntas frecuentes
- `Gallery` - Items de galería
- `Precio` - Precios
- `Location` - Ubicaciones
- `PDFSetting` - Configuración de PDF
- `ExtraModule` - Módulos extras
- `TestQuestion` - Preguntas de test

## ⚠️ Notas Importantes

1. **Compatibilidad**: El código legacy (`*_db.py`) sigue funcionando. La migración será gradual.

2. **Encriptación**: Los campos sensibles se cifran en el **repository**, no en el modelo. Los modelos almacenan datos cifrados.

3. **Relaciones**: Algunas relaciones (como `Bot` ↔ `Doctor`) se manejan manualmente por `admin_user_id` → `telegram_id` porque las tablas se crearon en momentos diferentes.

4. **Primary Keys Compuestas**: Algunos modelos como `TextContent` y `PDFSetting` tienen primary keys compuestas.

## 🧪 Pruebas

Ejecutar el script de prueba:

```bash
python scripts/test_sqlalchemy_setup.py
```

## ✅ Fase 2 - En Progreso

### Módulos Migrados

#### 1. `extra_modules_db.py` ✅

**Repository creado:**
- `ExtraModuleRepository` - Gestión completa de módulos extras

**Funciones migradas:**
- ✅ `get_active_modules_for_doctor()`
- ✅ `is_module_active_for_doctor()`
- ✅ `activate_module_for_doctor()`
- ✅ `deactivate_module_for_doctor()`
- ✅ `toggle_module_for_doctor()`
- ✅ `get_all_doctors_with_modules()`
- ✅ `get_available_modules()`

**Pruebas:**
```bash
python scripts/test_extra_module_repository.py
```

#### 2. `users_db.py` ✅

**Repositories creados:**
- `DoctorRepository` - Gestión completa de doctores
- `PatientDoctorRepository` - Gestión de asociaciones paciente-médico

**Funciones migradas:**
- ✅ `add_doctor()` - Crea doctor y bot asociado
- ✅ `get_doctor_by_telegram_id()` - Obtiene doctor activo
- ✅ `get_any_doctor_by_telegram_id()` - Obtiene doctor (activo o no)
- ✅ `get_doctor_by_id()` - Obtiene por ID
- ✅ `get_all_doctors()` - Lista todos los doctores activos
- ✅ `get_inactive_doctors()` - Lista doctores inactivos
- ✅ `delete_doctor()` - Marca como inactivo
- ✅ `remove_doctor_permanently()` - Elimina completamente
- ✅ `restrict_doctor()` - Restringe acceso
- ✅ `activate_doctor()` - Reactiva doctor
- ✅ `cleanup_doctor_patient_associations()` - Limpia asociaciones
- ✅ `assign_patient_to_doctor()` - Asigna paciente a doctor
- ✅ `get_doctor_for_patient()` - Obtiene doctor de un paciente
- ✅ `get_patients_for_doctor()` - Obtiene pacientes de un doctor
- ✅ `remove_association()` - Elimina asociación

**Compatibilidad:**
- `UsersDatabase` mantiene la misma interfaz síncrona
- Usa `asyncio.run()` internamente para compatibilidad
- Todo el código existente sigue funcionando sin cambios

**Pruebas:**
```bash
python scripts/test_user_repository.py
```

#### 3. `appointments_db.py` ✅

**Repositories creados:**
- `SlotRepository` - Gestión de slots (cupos de citas)
- `AppointmentRepository` - Gestión de appointments (citas reservadas)

**Funciones migradas:**

**SlotRepository:**
- ✅ `add_slot()` - Crea un nuevo slot
- ✅ `list_active_slots()` - Lista slots disponibles
- ✅ `delete_slot()` - Elimina un slot
- ✅ `get_slot_by_id()` - Obtiene slot por ID

**AppointmentRepository:**
- ✅ `book_slot()` - Reserva un slot para un paciente
- ✅ `get_appointments_for_doctor()` - Obtiene citas de un doctor
- ✅ `get_appointment_by_id()` - Obtiene cita por ID
- ✅ `update_appointment_status()` - Actualiza estado de cita
- ✅ `update_appointment_time()` - Actualiza tiempo de cita
- ✅ `delete_appointment()` - Elimina cita y su slot

**Compatibilidad:**
- `AppointmentsDB` mantiene la misma interfaz síncrona
- Usa `asyncio.run()` internamente para compatibilidad
- Todo el código existente sigue funcionando sin cambios

**Pruebas:**
```bash
python scripts/test_appointment_repository.py
```

#### 4. `content_db.py` ✅

**Repositories creados:**
- `TextContentRepository` - Gestión de text_content (contenido configurable)
- `GenericContentRepository` - Gestión genérica de tablas dinámicas (FAQs, Gallery, Precios, etc.)

**Funciones migradas:**

**TextContentRepository:**
- ✅ `get_content()` - Obtiene contenido por clave
- ✅ `update_content()` - Actualiza o inserta contenido
- ✅ `delete_content_by_key()` - Elimina contenido por clave
- ✅ `get_next_custom_text_id()` - Obtiene siguiente ID para textos personalizados
- ✅ `get_submenu_headers()` - Obtiene encabezados de submenús

**GenericContentRepository:**
- ✅ `get_all_items()` - Lista todos los items de una tabla
- ✅ `get_item_details()` - Obtiene detalles de un item
- ✅ `add_item()` - Añade un nuevo item
- ✅ `update_item()` - Actualiza un item
- ✅ `delete_item()` - Elimina un item
- ✅ `reorder_item()` - Reordena items
- ✅ `get_item_content()` - Obtiene solo el contenido de un item
- ✅ `get_item_details_with_media()` - Obtiene detalles con media
- ✅ `update_item_with_media()` - Actualiza item con media
- ✅ `add_item_with_media()` - Añade item con media

**Compatibilidad:**
- `content_db.py` mantiene la misma interfaz asíncrona
- Todo el código existente sigue funcionando sin cambios
- Validación de nombres de tabla/columna para seguridad

**Notas:**
- Usa `text()` de SQLAlchemy para queries dinámicos de forma segura
- Valida nombres de tabla/columna antes de construir queries
- Soporta operaciones con y sin media (fotos/videos)

#### 5. `locations_db.py` ✅

**Repository creado:**
- `LocationRepository` - Gestión completa de ubicaciones

**Funciones migradas:**
- ✅ `get_location_details()` - Obtiene detalles de una ubicación
- ✅ `add_location()` - Añade nueva ubicación
- ✅ `update_location()` - Actualiza ubicación existente
- ✅ `delete_location()` - Elimina ubicación
- ✅ `get_locations_for_bot()` - Obtiene ubicaciones activas de un bot

**Compatibilidad:**
- `locations_db.py` mantiene la misma interfaz asíncrona
- Todo el código existente sigue funcionando sin cambios

#### 6. `preconsulta_db.py` ✅

**Repository creado:**
- `MedicalRepository` - Gestión completa de historiales médicos con encriptación automática

**Funciones migradas:**
- ✅ `save_history()` - Guarda nueva historia (cifra campos sensibles)
- ✅ `get_history_details()` - Obtiene detalles (descifra campos sensibles)
- ✅ `complete_history()` - Completa historia con datos del admin (cifra)
- ✅ `delete_history()` - Elimina historia
- ✅ `get_latest_completed_histories()` - Lista historiales completados recientes
- ✅ `search_completed_histories_by_name()` - Busca por nombre (descifra en memoria)
- ✅ `check_if_user_is_recurrent()` - Verifica si es paciente recurrente
- ✅ `get_all_histories()` - Lista historiales pendientes (paginado)
- ✅ `get_patient_history_list()` - Lista historiales de un paciente
- ✅ `update_history_field()` - Actualiza campo específico (cifra si es sensible)
- ✅ `get_next_history_number()` - Genera número de historia correlativo
- ✅ `save_history_number()` - Guarda número de historia

**Encriptación:**
- Cifra automáticamente campos sensibles antes de guardar
- Descifra automáticamente campos sensibles después de leer
- Lista de campos sensibles: `SENSITIVE_FIELDS` (37 campos)
- Compatible con datos antiguos no cifrados

**Compatibilidad:**
- `preconsulta_db.py` mantiene la misma interfaz asíncrona
- Todo el código existente sigue funcionando sin cambios
- Re-exporta `SENSITIVE_FIELDS` para compatibilidad

**Notas:**
- La búsqueda por nombre descifra en memoria (no ideal para grandes volúmenes)
- Validación de nombres de columnas para prevenir SQL injection
- Manejo automático de encriptación/desencriptación transparente

#### 7. `pdf_configuration/database.py` ✅

**Repository creado:**
- `PDFRepository` - Gestión completa de configuración de PDF

**Funciones migradas:**
- ✅ `get_pdf_settings()` - Obtiene toda la configuración (aplica defaults)
- ✅ `apply_default_settings()` - Aplica valores por defecto
- ✅ `update_pdf_setting()` - Actualiza o crea configuración
- ✅ `toggle_setting_visibility()` - Alterna visibilidad
- ✅ `get_setting_value()` - Obtiene valor específico

**Compatibilidad:**
- `pdf_configuration/database.py` mantiene la misma interfaz asíncrona
- Re-exporta `DEFAULT_PDF_SETTINGS` para compatibilidad
- Todo el código existente sigue funcionando sin cambios

**Notas:**
- Maneja primary key compuesta (doctor_id, setting_key)
- Aplica valores por defecto automáticamente si faltan configuraciones

## 📊 Resumen del Progreso

### Módulos Migrados: 7/10+ ✅

1. ✅ `extra_modules_db.py` - ExtraModuleRepository
2. ✅ `users_db.py` - DoctorRepository, PatientDoctorRepository
3. ✅ `appointments_db.py` - SlotRepository, AppointmentRepository
4. ✅ `content_db.py` - TextContentRepository, GenericContentRepository
5. ✅ `locations_db.py` - LocationRepository
6. ✅ `preconsulta_db.py` - MedicalRepository (con encriptación)
7. ✅ `pdf_configuration/database.py` - PDFRepository

### Repositories Creados: 10

- ExtraModuleRepository
- DoctorRepository
- PatientDoctorRepository
- SlotRepository
- AppointmentRepository
- TextContentRepository
- GenericContentRepository
- LocationRepository
- MedicalRepository
- PDFRepository

### Estado de Compatibilidad

- ✅ 100% Compatible - Todo el código legacy sigue funcionando
- ✅ Encriptación funcionando correctamente
- ✅ Validación de seguridad implementada
- ✅ Tests pasando

## 📅 Próximos Pasos (Fase 2 - Continuación)

1. ✅ ~~Crear ExtraModuleRepository~~ - Completado
2. ✅ ~~Crear UserRepository~~ - Completado
3. ✅ ~~Crear AppointmentRepository~~ - Completado
4. ✅ ~~Crear ContentRepository~~ - Completado
5. ✅ ~~Crear LocationRepository~~ - Completado
6. ✅ ~~Crear MedicalRepository~~ - Completado
7. ✅ ~~Crear PDFRepository~~ - Completado
8. ✅ ~~Migrar módulos restantes menores~~ - Completado (todos tienen repositories)
9. ✅ ~~Configurar Alembic para migraciones de esquema~~ - Completado y aplicado
10. ⏳ Optimizar queries y relaciones

## 🔗 Referencias

- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)

