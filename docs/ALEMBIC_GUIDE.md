# 📚 Guía de Uso de Alembic

## Configuración

Alembic está configurado para trabajar con SQLAlchemy asíncrono y SQLite. La configuración se encuentra en:
- `alembic.ini` - Configuración general
- `alembic/env.py` - Configuración del entorno (usa SQLAlchemy asíncrono)

## Comandos Principales

### 1. Crear una Nueva Migración

Para crear una nueva migración basada en los cambios en los modelos:

```bash
cd gynsys
alembic revision --autogenerate -m "Descripción de los cambios"
```

**Ejemplo:**
```bash
alembic revision --autogenerate -m "Agregar campo nuevo a tabla doctors"
```

### 2. Crear una Migración Manual

Si necesitas crear una migración manual (sin autogenerate):

```bash
alembic revision -m "Descripción de los cambios"
```

Luego edita el archivo generado en `alembic/versions/` para agregar las operaciones SQL necesarias.

### 3. Aplicar Migraciones

Para aplicar todas las migraciones pendientes:

```bash
alembic upgrade head
```

Para aplicar hasta una versión específica:

```bash
alembic upgrade <revision_id>
```

### 4. Revertir Migraciones

Para revertir a la versión anterior:

```bash
alembic downgrade -1
```

Para revertir a una versión específica:

```bash
alembic downgrade <revision_id>
```

### 5. Ver el Estado Actual

Para ver el estado actual de las migraciones:

```bash
alembic current
```

Para ver el historial de migraciones:

```bash
alembic history
```

### 6. Ver SQL de una Migración

Para ver el SQL que se ejecutará sin aplicarlo:

```bash
alembic upgrade head --sql
```

## Flujo de Trabajo Recomendado

### Desarrollo de una Nueva Característica

1. **Modificar los modelos** en `database/models/`
2. **Crear la migración:**
   ```bash
   alembic revision --autogenerate -m "Agregar nueva tabla X"
   ```
3. **Revisar la migración generada** en `alembic/versions/`
4. **Aplicar la migración:**
   ```bash
   alembic upgrade head
   ```
5. **Probar la aplicación** para verificar que todo funciona

### Modificar una Migración Existente

⚠️ **ADVERTENCIA:** Solo modifica migraciones que aún no se han aplicado en producción.

1. Edita el archivo de migración en `alembic/versions/`
2. Si ya se aplicó, crea una nueva migración para revertir y reaplicar

## Estructura de Archivos

```
gynsys/
├── alembic.ini              # Configuración de Alembic
├── alembic/
│   ├── env.py               # Configuración del entorno (async)
│   ├── script.py.mako       # Plantilla para nuevas migraciones
│   └── versions/            # Migraciones (archivos .py)
│       └── xxxx_initial.py  # Migración inicial
└── database/
    └── models/              # Modelos SQLAlchemy
```

## Migración Inicial

La primera vez que uses Alembic, necesitas crear la migración inicial que refleje el estado actual de la base de datos:

```bash
# 1. Crear la migración inicial
alembic revision --autogenerate -m "Initial migration"

# 2. Revisar el archivo generado (importante verificar que sea correcto)

# 3. Aplicar la migración
alembic upgrade head
```

## Notas Importantes

### ⚠️ SQLite y Alembic

- SQLite tiene limitaciones con `ALTER TABLE`. Algunas operaciones requieren recrear la tabla.
- Alembic maneja esto automáticamente, pero revisa las migraciones generadas.

### 🔒 Backup Antes de Migrar

**SIEMPRE haz un backup de la base de datos antes de aplicar migraciones en producción:**

```bash
# Backup manual
cp database/medical_bot.db database/medical_bot.db.backup
```

### 🔍 Revisar Migraciones Generadas

Alembic puede generar migraciones incorrectas o incompletas. **SIEMPRE revisa** el archivo generado antes de aplicarlo, especialmente:

- Operaciones de `ALTER TABLE` en SQLite
- Cambios en constraints o índices
- Operaciones de datos (INSERT, UPDATE, DELETE)

### 📝 Convenciones de Nombres

Usa nombres descriptivos para las migraciones:

- ✅ `add_user_email_field`
- ✅ `create_notifications_table`
- ✅ `add_foreign_key_to_appointments`
- ❌ `migration1`
- ❌ `changes`

## Solución de Problemas

### Error: "Target database is not up to date"

**Solución:** Aplica las migraciones pendientes:
```bash
alembic upgrade head
```

### Error: "Can't locate revision identified by 'xxxx'"

**Solución:** Verifica que todas las migraciones estén en `alembic/versions/` y que el historial sea consistente.

### Error: "Multiple heads detected"

**Solución:** Tienes múltiples ramas de migraciones. Fusiona las ramas:
```bash
alembic merge heads -m "Merge branches"
```

## Recursos Adicionales

- [Documentación oficial de Alembic](https://alembic.sqlalchemy.org/)
- [Alembic con SQLAlchemy asíncrono](https://alembic.sqlalchemy.org/en/latest/branches.html#working-with-async-engines)
- [SQLite y Alembic](https://alembic.sqlalchemy.org/en/latest/batch.html)


