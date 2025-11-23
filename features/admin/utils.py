"""
Helpers genéricos para el módulo admin.
Funciones utilitarias compartidas: paginación, safe_edit, etc.
"""
import math
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest


def paginate(items, page, page_size=7):
    """
    Pagina una lista de items.
    
    Args:
        items: Lista de items a paginar
        page: Número de página (0-indexed)
        page_size: Tamaño de página (default: 7)
    
    Returns:
        tuple: (items_paginados, página_actual, total_páginas)
    """
    total_pages = max(1, math.ceil(len(items) / page_size))
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    return items[start:start + page_size], page, total_pages


async def safe_edit_message(query, text, reply_markup, context, parse_mode="Markdown"):
    """
    Helper para editar mensajes de forma segura, manejando el caso cuando
    el mensaje anterior es una imagen.
    
    Args:
        query: CallbackQuery de Telegram
        text: Texto del mensaje
        reply_markup: Teclado inline
        context: ContextTypes.DEFAULT_TYPE
        parse_mode: Modo de parseo (default: "Markdown")
    """
    try:
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except BadRequest as e:
        # Si el mensaje es una foto (no tiene texto), eliminar primero
        if "no text" in str(e).lower() or "message to edit not found" in str(e).lower():
            try:
                await query.message.delete()
            except:
                pass
            # Luego enviar nuevo mensaje con texto y botones
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            # Otro error, enviar nuevo mensaje
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )


def generate_share_code(doctor_id: int) -> str:
    """
    Genera un código de compartir para un médico.
    
    Args:
        doctor_id: ID del médico
    
    Returns:
        str: Código de compartir (ej: "gynsysbot000001")
    """
    return f"gynsysbot{doctor_id:06d}"

