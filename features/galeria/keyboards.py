# features/galeria/keyboards.py
from typing import Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import content_db

CONFIG = {'prefix': 'gallery'} # Prefijo por defecto para callbacks

async def get_galeria_keyboard(tenant_id: int):
    """Muestra la lista de ítems de la Galería al usuario final."""
    items = await content_db.get_all_items(tenant_id, 'gallery', 'title')
    keyboard = [[InlineKeyboardButton(item['title'], callback_data=f"{CONFIG['prefix']}_item_{item['id']}")] for item in items]
    keyboard.append([InlineKeyboardButton("🏠 Menú Principal", callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)

async def get_gallery_for_action_keyboard(
    tenant_id: int,
    action: str,
    prefix: str = CONFIG['prefix'],
    back_callback: Optional[str] = None,
):
    """Muestra la lista de ítems para que el admin los gestione."""
    items = await content_db.get_all_items(tenant_id, 'gallery', 'title')
    if not items:
        return None

    emoji = "✏️" if action == "modify" else "🗑️"
    keyboard = [
        [
            InlineKeyboardButton(
                f"{emoji} {item['title']}",
                callback_data=f"{prefix}_{action}_{item['id']}"
            )
        ]
        for item in items
    ]

    back_callback = back_callback or (f"{prefix}_admin_hub" if prefix == 'gallery' else f"{prefix}_hub")
    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data=back_callback)])
    return InlineKeyboardMarkup(keyboard)

async def get_gallery_reorder_keyboard(
    tenant_id: int,
    prefix: str = CONFIG['prefix'],
    done_callback: Optional[str] = None,
):
    """Muestra la lista de ítems con botones para reordenar."""
    items = await content_db.get_all_items(tenant_id, 'gallery', 'title')
    if not items or len(items) < 2:
        return None

    min_order = min(it['display_order'] for it in items)
    max_order = max(it['display_order'] for it in items)

    keyboard = []
    for item in items:
        row = [InlineKeyboardButton(item['title'], callback_data="ignore")]
        if item['display_order'] > min_order:
            row.append(InlineKeyboardButton("🔼", callback_data=f"{prefix}_reorder_up_{item['id']}"))
        if item['display_order'] < max_order:
            row.append(InlineKeyboardButton("🔽", callback_data=f"{prefix}_reorder_down_{item['id']}"))
        keyboard.append(row)

    done_callback = done_callback or (f"{prefix}_admin_hub" if prefix == 'gallery' else f"{prefix}_hub")
    keyboard.append([InlineKeyboardButton("✅ Listo", callback_data=done_callback)])
    return InlineKeyboardMarkup(keyboard)