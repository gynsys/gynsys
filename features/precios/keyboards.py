# features/precios/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import content_db

# --- FUNCIÓN RENOMBRADA ---
async def get_precios_keyboard(bot_id: int):
    """Muestra la lista de precios al usuario final."""
    items = await content_db.get_all_items(bot_id, 'precios', 'title')

    # --- ¡CORRECCIÓN AQUÍ! ---
    # Cambiamos "price_item_" a "precio_item_" para que coincida con el handler.
    keyboard = [[InlineKeyboardButton(item['title'], callback_data=f"precio_item_{item['id']}")] for item in items]

    keyboard.append([InlineKeyboardButton("🏠 Menú Principal", callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)

# --- Teclados para el ADMIN (con nombres estandarizados) ---
async def get_precios_for_action_keyboard(bot_id: int, action: str):
    """Muestra la lista de Precios para que el admin los modifique o elimine."""
    items = await content_db.get_all_items(bot_id, 'precios', 'title')
    if not items: return None

    emoji = "✏️" if action == "modify" else "🗑️"
    keyboard = [[InlineKeyboardButton(f"{emoji} {item['title']}", callback_data=f"precio_{action}_{item['id']}")] for item in items]
    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="prices_admin_hub")])
    return InlineKeyboardMarkup(keyboard)

async def get_precios_reorder_keyboard(bot_id: int):
    """Muestra la lista de Precios con botones para reordenar."""
    items = await content_db.get_all_items(bot_id, 'precios', 'title')
    if not items or len(items) < 2: return None

    keyboard = []
    for i, item in enumerate(items):
        row = [InlineKeyboardButton(item['title'], callback_data="ignore")]
        if i > 0: row.append(InlineKeyboardButton("🔼", callback_data=f"precio_reorder_up_{item['id']}"))
        if i < len(items) - 1: row.append(InlineKeyboardButton("🔽", callback_data=f"precio_reorder_down_{item['id']}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("✅ Listo", callback_data="prices_admin_hub")])
    return InlineKeyboardMarkup(keyboard)