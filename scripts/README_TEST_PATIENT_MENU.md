# Script de Prueba: patient_main_menu con FakeUpdate

## Descripción

Este script simula el escenario exacto donde `finish_preconsultation` crea un `FakeUpdate` y llama a `patient_main_menu`, permitiendo probar el flujo sin ejecutar el bot completo.

## Ubicación

`scripts/test_patient_main_menu.py`

## Uso

### 1. Ajustar la configuración

Antes de ejecutar, edita las variables en el script:

```python
TEST_CHAT_ID = 123456789      # ID del chat de prueba
TEST_USER_ID = 123456789      # ID del usuario de prueba  
TEST_DOCTOR_ID = 1            # ID del doctor en la BD (debe existir)
TEST_USER_NAME = "Paciente Prueba"  # Nombre del usuario
```

**Importante:** El `TEST_DOCTOR_ID` debe ser un doctor válido que exista en tu base de datos.

### 2. Ejecutar el script

Desde el directorio raíz del proyecto:

```bash
python scripts/test_patient_main_menu.py
```

O desde el directorio `scripts/`:

```bash
cd scripts
python test_patient_main_menu.py
```

## Qué hace el script

1. ✅ Crea un `FakeUpdate` idéntico al que se crea en `finish_preconsultation`
2. ✅ Simula un `context` con un bot fake
3. ✅ Llama a `patient_main_menu` con estos objetos simulados
4. ✅ Muestra el mensaje que se enviaría (sin enviarlo realmente)
5. ✅ Muestra el teclado que se generaría
6. ✅ Captura y muestra cualquier error que ocurra

## Salida esperada

El script mostrará:

- 📋 Configuración de prueba
- ✅ Detalles del FakeUpdate creado
- 📤 El mensaje que se enviaría al bot (con formato)
- 🎹 El teclado con los botones generados
- ✅ Confirmación de éxito o ❌ detalles del error

## Ventajas

- ✅ **No modifica archivos del proyecto**: Es completamente externo
- ✅ **Simula exactamente el escenario real**: Usa el mismo `FakeUpdate` que `finish_preconsultation`
- ✅ **Fácil de depurar**: Muestra toda la información relevante
- ✅ **No requiere ejecutar el bot**: Prueba solo la función específica

## Notas

- El script usa la base de datos real del proyecto (lee `DB_PATH` de `config.py`)
- Asegúrate de que el `TEST_DOCTOR_ID` exista en tu base de datos
- El script no envía mensajes reales, solo los simula y muestra

