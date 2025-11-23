# features/faqs/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import content_db

# --- Teclados para el USUARIO ---
async def get_faq_keyboard(bot_id: int):
    """Muestra la lista de preguntas frecuentes al usuario final."""
    items = await content_db.get_all_items(bot_id, 'faqs', 'question')
    keyboard = []
    if items:
        keyboard = [[InlineKeyboardButton(item['title'], callback_data=f"faq_item_{item['id']}")] for item in items]
    
    keyboard.append([InlineKeyboardButton("🏠 Menú Principal", callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)

# --- Teclados para el ADMIN ---
async def get_faqs_for_action_keyboard(bot_id: int, action: str):
    """Muestra la lista de FAQs para que el admin las modifique o elimine."""
    items = await content_db.get_all_items(bot_id, 'faqs', 'question')
    if not items: 
        return None
    
    emoji = "✏️" if action == "modify" else "🗑️"
    keyboard = [[InlineKeyboardButton(
        f"{emoji} {item['title']}", callback_data=f"faq_{action}_{item['id']}"
    )] for item in items]
    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="faqs_admin_hub")])
    return InlineKeyboardMarkup(keyboard)

async def get_faqs_reorder_keyboard(bot_id: int):
    """Muestra la lista de FAQs con botones para reordenar."""
    items = await content_db.get_all_items(bot_id, 'faqs', 'question')
    if not items or len(items) < 2:
        return None
        
    keyboard = []
    for i, item in enumerate(items):
        row = [InlineKeyboardButton(item['title'], callback_data="ignore")]
        if i > 0: row.append(InlineKeyboardButton("🔼", callback_data=f"faq_reorder_up_{item['id']}"))
        if i < len(items) - 1: row.append(InlineKeyboardButton("🔽", callback_data=f"faq_reorder_down_{item['id']}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("✅ Listo", callback_data="faqs_admin_hub")])
    return InlineKeyboardMarkup(keyboard)