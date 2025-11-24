# Flujo Completo: Cita → Decisión HO (Historial Obstétrico)

## 📋 Resumen del Flujo

Este documento mapea todas las funciones involucradas desde la solicitud de cita hasta la decisión de entrar al flujo del historial obstétrico (HO).

---

## 🔄 FLUJO PASO A PASO

### **FASE 1: Solicitud de Cita**

#### 1.1. Selección de Tipo de Consulta
- **Función**: `handle_consultation_type` (línea ~200)
- **Archivo**: `features/citas/user_handlers.py`
- **Acción**: Guarda `booking_consultation_type` en `context.user_data`
- **Valores posibles**: `'Prenatal'` o `'Ginecológica'`

#### 1.2. Pregunta sobre Embarazo (según tipo)
- **Función**: `handle_consultation_type` → retorna `AWAITING_PREGNANCY_INFO`
- **Archivo**: `features/citas/user_handlers.py`
- **Muestra teclado**: 
  - Si `Prenatal`: pregunta "¿Es tu primer embarazo?"
  - Si `Ginecológica`: pregunta "¿Has estado embarazada alguna vez?"

#### 1.3. Captura de Respuesta sobre Embarazo
- **Función**: `handle_pregnancy_info` (línea 229)
- **Archivo**: `features/citas/user_handlers.py`
- **Patrón callback**: `^book_(first|ever)_preg_`
- **Lógica**:
  ```python
  if consultation_type == 'Prenatal':
      context.user_data['booking_is_first_pregnancy'] = query.data.endswith('_yes')
  else: # Ginecológica
      context.user_data['booking_has_been_pregnant'] = query.data.endswith('_yes')
  ```
- **Estado**: Retorna `AWAITING_REASON`

#### 1.4. Confirmación de Cita
- **Función**: `confirm_appointment` (línea 565)
- **Archivo**: `features/citas/user_handlers.py`
- **Obtiene valores**:
  ```python
  consultation_type = ud.get('booking_consultation_type', 'Ginecológica')
  is_first_pregnancy = ud.get('booking_is_first_pregnancy')
  has_been_pregnant = ud.get('booking_has_been_pregnant')
  ```
- **Llama a**: `_create_appointment()` pasando estos valores

---

### **FASE 2: Guardado en Base de Datos**

#### 2.1. Creación de Appointment
- **Función**: `_create_appointment` (línea 72)
- **Archivo**: `features/citas/user_handlers.py`
- **Parámetros recibidos**:
  - `consultation_type`
  - `is_first_pregnancy`
  - `has_been_pregnant`
- **Llama a**: `appointment_repo.book_slot()` pasando estos valores

#### 2.2. Guardado en Repository
- **Función**: `book_slot` (línea 145)
- **Archivo**: `database/repositories/appointment_repository.py`
- **Acción**: Crea objeto `Appointment` con:
  ```python
  Appointment(
      ...
      consultation_type=consultation_type,
      is_first_pregnancy=is_first_pregnancy,
      has_been_pregnant=has_been_pregnant,
      ...
  )
  ```
- **Guarda en BD**: `await self.session.flush()`

---

### **FASE 3: Inicio de Preconsulta**

#### 3.1. Inicio del Flujo
- **Función**: `start_preconsultation_flow` (línea 261)
- **Archivo**: `features/preconsulta/patient_flow/generic_flow_engine.py`
- **Obtiene**: `appointment_id` del callback_data

#### 3.2. Carga de Datos de la Cita
- **Función**: `appointment_repo.get_appointment_by_id()` (línea 294)
- **Archivo**: `database/repositories/appointment_repository.py` (línea 257)
- **Retorna diccionario con**:
  ```python
  {
      'consultation_type': appointment.consultation_type,
      'is_first_pregnancy': getattr(appointment, 'is_first_pregnancy', None),
      'has_been_pregnant': getattr(appointment, 'has_been_pregnant', None),
      ...
  }
  ```

#### 3.3. Carga en Contexto
- **Función**: `start_preconsultation_flow` (línea 312-314)
- **Archivo**: `features/preconsulta/patient_flow/generic_flow_engine.py`
- **Carga en context.user_data**:
  ```python
  context.user_data['consultation_type'] = appointment_dict.get('consultation_type')
  context.user_data['is_first_pregnancy'] = appointment_dict.get('is_first_pregnancy')
  context.user_data['has_been_pregnant'] = appointment_dict.get('has_been_pregnant')
  ```

---

### **FASE 4: Decisión del Flujo Obstétrico**

#### 4.1. Función de Decisión
- **Función**: `decide_obstetric_flow` (línea 21)
- **Archivo**: `features/preconsulta/flow_actions/handlers/obstetric_handlers.py`
- **Obtiene valores de context.user_data**:
  ```python
  consultation_type = user_data.get('consultation_type')
  is_first_pregnancy = user_data.get('is_first_pregnancy')
  has_been_pregnant = user_data.get('has_been_pregnant')
  ```

#### 4.2. Lógica de los 4 Casos
- **CASO 1**: `Prenatal` + `is_first_pregnancy == True`
  - → **NO entra a HO**
  - → Asigna fórmula: `G1 P0 A0 C0. Primigesta`
  - → Retorna: `node['next_if_skip']`

- **CASO 2**: `Prenatal` + `is_first_pregnancy == False`
  - → **SÍ entra a HO**
  - → Retorna: `node['next_if_needed']`

- **CASO 3**: `Ginecológica` + `has_been_pregnant == False`
  - → **NO entra a HO**
  - → Asigna fórmula: `G0 P0 A0 C0. Nuligesta`
  - → Retorna: `node['next_if_skip']`

- **CASO 4**: `Ginecológica` + `has_been_pregnant == True`
  - → **SÍ entra a HO**
  - → Retorna: `node['next_if_needed']`

---

## ✅ VERIFICACIÓN DE FUNCIONES

### Funciones de Captura (Citas)
- ✅ `handle_consultation_type` - Guarda tipo de consulta
- ✅ `handle_pregnancy_info` - Captura respuesta sobre embarazo (AMBOS casos)
- ⚠️ `handle_ever_pregnant` - **NO SE USA** (código muerto, línea 475)
- ⚠️ `handle_first_pregnancy` - **NO SE USA** (código muerto, línea 505)

### Funciones de Guardado
- ✅ `confirm_appointment` - Obtiene valores y llama a `_create_appointment`
- ✅ `_create_appointment` - Pasa valores a `book_slot`
- ✅ `book_slot` - Guarda en `Appointment` con ambos campos

### Funciones de Carga
- ✅ `start_preconsultation_flow` - Inicia flujo y carga datos
- ✅ `get_appointment_by_id` - Retorna diccionario con ambos campos
- ✅ Carga en `context.user_data` - Los 3 valores se cargan correctamente

### Funciones de Decisión
- ✅ `decide_obstetric_flow` - Usa los 3 valores para decidir
- ✅ Lógica de 4 casos - Todos implementados correctamente

---

## 🔍 PUNTOS CRÍTICOS VERIFICADOS

1. ✅ **Modelo Appointment**: Tiene campos `is_first_pregnancy` y `has_been_pregnant`
2. ✅ **Repository book_slot**: Acepta y guarda ambos campos
3. ✅ **Repository get_appointment_by_id**: Retorna ambos campos en el diccionario
4. ✅ **confirm_appointment**: Pasa valores originales (no calculados)
5. ✅ **start_preconsultation_flow**: Carga ambos campos en context.user_data
6. ✅ **decide_obstetric_flow**: Usa ambos campos correctamente

---

## ⚠️ NOTAS

- Las funciones `handle_ever_pregnant` y `handle_first_pregnancy` están definidas pero NO se usan.
- El ConversationHandler solo registra `handle_pregnancy_info` que maneja ambos casos.
- Esto está correcto y no causa problemas.

---

## 🧪 PRUEBAS

- ✅ Script `test_complete_obstetric_flow.py`: Prueba flujo completo
- ✅ Todas las 4 pruebas pasaron exitosamente
- ✅ Valores se guardan y cargan correctamente
- ✅ Decisión funciona para todos los casos

