-- Eliminar mensaje de bienvenida para bot_id=2 (MARI)
DELETE FROM text_content WHERE key = 'msg_bienvenida_editable' AND bot_id = 2;

-- Verificar que se eliminó
SELECT * FROM text_content WHERE key = 'msg_bienvenida_editable' AND bot_id = 2;

