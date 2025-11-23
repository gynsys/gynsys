# Comandos SQL para Verificar Mensaje de Bienvenida

## 1. Ver todos los mensajes de bienvenida
```sql
SELECT 
    bot_id, 
    key, 
    LENGTH(value) as longitud,
    SUBSTR(value, 1, 100) as preview
FROM text_content 
WHERE key = 'msg_bienvenida_editable'
ORDER BY bot_id;
```

## 2. Ver el mensaje completo para bot_id = 2 (MARI)
```sql
SELECT 
    bot_id, 
    key, 
    value,
    LENGTH(value) as longitud
FROM text_content 
WHERE key = 'msg_bienvenida_editable' AND bot_id = 2;
```

## 3. Ver todos los bot_id y sus mensajes de bienvenida
```sql
SELECT 
    b.id as bot_id,
    b.doctor_name,
    b.admin_user_id,
    tc.value as mensaje_bienvenida,
    LENGTH(tc.value) as longitud
FROM bots b
LEFT JOIN text_content tc ON tc.bot_id = b.id AND tc.key = 'msg_bienvenida_editable'
WHERE b.is_active = 1
ORDER BY b.id;
```

## 4. Verificar información de MARI (Doctor ID 279)
```sql
SELECT 
    d.id as doctor_id,
    d.name as doctor_name,
    d.telegram_id,
    b.id as bot_id,
    b.doctor_name as bot_name,
    b.admin_user_id
FROM doctors d
LEFT JOIN bots b ON b.admin_user_id = d.telegram_id
WHERE d.id = 279 OR d.telegram_id = 5057356565;
```

## 5. Ver todos los registros de text_content para bot_id = 2
```sql
SELECT 
    key,
    value,
    LENGTH(value) as longitud
FROM text_content 
WHERE bot_id = 2
ORDER BY key;
```

## 6. Contar cuántos mensajes de bienvenida hay por bot_id
```sql
SELECT 
    bot_id,
    COUNT(*) as total_mensajes
FROM text_content 
WHERE key = 'msg_bienvenida_editable'
GROUP BY bot_id;
```

## 7. Ver el mensaje más reciente (si hay timestamp)
```sql
SELECT 
    bot_id,
    key,
    value,
    LENGTH(value) as longitud
FROM text_content 
WHERE key = 'msg_bienvenida_editable' AND bot_id = 2
ORDER BY rowid DESC
LIMIT 1;
```

## 8. Verificar si hay duplicados
```sql
SELECT 
    bot_id,
    COUNT(*) as cantidad
FROM text_content 
WHERE key = 'msg_bienvenida_editable'
GROUP BY bot_id
HAVING COUNT(*) > 1;
```

## 9. Ver todos los bot_id disponibles
```sql
SELECT 
    id as bot_id,
    doctor_name,
    admin_user_id,
    is_active
FROM bots
ORDER BY id;
```

## 10. Ver el mensaje completo con formato legible
```sql
SELECT 
    'Bot ID: ' || bot_id || CHAR(10) ||
    'Key: ' || key || CHAR(10) ||
    'Longitud: ' || LENGTH(value) || ' caracteres' || CHAR(10) ||
    'Mensaje:' || CHAR(10) || value as resultado
FROM text_content 
WHERE key = 'msg_bienvenida_editable' AND bot_id = 2;
```

