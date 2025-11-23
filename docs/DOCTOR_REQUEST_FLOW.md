# Flujo Crítico: Solicitud de Nuevo Inquilino (Doctor Request)

## ⚠️ IMPORTANTE

Este flujo es **CRÍTICO** para el onboarding de nuevos inquilinos. Cualquier modificación debe hacerse con extremo cuidado y probarse exhaustivamente.

## Descripción del Flujo

1. Usuario hace clic en "Solicitar Bot" → `start_request_bot()`
2. Bot pide nombre → Estado: `REQUEST_WAITING_NAME`
3. Usuario envía nombre → `receive_full_name()` → **DEBE retornar** `REQUEST_WAITING_TELEGRAM_ID`
4. Bot pide ID de Telegram → Estado: `REQUEST_WAITING_TELEGRAM_ID`
5. Usuario envía ID → `receive_telegram_id()` → **DEBE retornar** `ConversationHandler.END`
6. Se crea la solicitud y se notifica al superadmin

## Archivos Involucrados

- `features/doctor_requests/handler.py` - Lógica del flujo
- `handlers/registration.py` - Registro del ConversationHandler (línea ~118-135)

## Puntos Críticos

### 1. `receive_full_name()` DEBE retornar `REQUEST_WAITING_TELEGRAM_ID`

```python
async def receive_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... código ...
    return REQUEST_WAITING_TELEGRAM_ID  # ⚠️ CRÍTICO: Este return NO debe cambiar
```

**Si este return no se ejecuta o retorna otro valor, el flujo se rompe y el bot no pedirá el ID.**

### 2. El ConversationHandler debe estar registrado ANTES de handlers genéricos

En `handlers/registration.py`, el `request_bot_conv` debe registrarse **antes** de cualquier handler genérico de mensajes que pueda interceptar los mensajes de texto.

### 3. Los estados del ConversationHandler

```python
REQUEST_WAITING_NAME, REQUEST_WAITING_TELEGRAM_ID = range(2)
```

**NO modificar estos valores** sin actualizar también el ConversationHandler.

## Errores Comunes que Rompen el Flujo

1. **Modificar el return de `receive_full_name()`**
   - ❌ Retornar `ConversationHandler.END` por error
   - ❌ No retornar nada (retorna `None`)
   - ❌ Retornar un valor diferente

2. **Agregar handlers genéricos antes del ConversationHandler**
   - ❌ Registrar un `MessageHandler(filters.TEXT)` antes de `request_bot_conv`
   - Esto interceptaría los mensajes antes de que lleguen al ConversationHandler

3. **Modificar `user_data` incorrectamente**
   - ❌ Limpiar `context.user_data` durante el flujo
   - ❌ Sobrescribir `doctor_request_name` o `doctor_request_message`

4. **Cambiar los nombres de los estados**
   - ❌ Renombrar `REQUEST_WAITING_NAME` o `REQUEST_WAITING_TELEGRAM_ID`
   - Esto rompería el ConversationHandler

## Cómo Probar el Flujo

1. Iniciar el bot
2. Hacer clic en "Solicitar Bot"
3. Enviar un nombre (ej: "Ada Test")
4. **VERIFICAR**: El bot debe pedir el ID de Telegram
5. Enviar un ID numérico (ej: "123456789")
6. **VERIFICAR**: Se debe crear la solicitud y mostrar mensaje de éxito

## Logging

El flujo ahora incluye logging detallado. Si el flujo se rompe, revisar los logs para:
- Ver si `receive_full_name()` se está ejecutando
- Ver qué valor está retornando
- Ver si hay errores silenciosos

## Checklist Antes de Modificar

- [ ] ¿Realmente necesito modificar este flujo?
- [ ] ¿He leído este documento completo?
- [ ] ¿He probado el flujo completo después de mis cambios?
- [ ] ¿He verificado que `receive_full_name()` retorna `REQUEST_WAITING_TELEGRAM_ID`?
- [ ] ¿He verificado que no hay handlers genéricos interceptando mensajes?
- [ ] ¿He agregado logging para debugging?

## Contacto

Si necesitas modificar este flujo y no estás seguro, consulta con el equipo antes de hacer cambios.

