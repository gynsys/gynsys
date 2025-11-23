# features/ubicaciones/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import content_db


# --- Teclados para el USUARIO ---
async def get_ubicaciones_keyboard(bot_id: int, home_callback: str):
    """Crea un teclado con una lista de todas las ubicaciones para el usuario."""
    locations = await content_db.get_all_items(bot_id, 'locations', 'name')
    keyboard = [
        [InlineKeyboardButton(f"📍 {loc['title']}", callback_data=f"sede_select_{loc['id']}")]
        for loc in locations
    ]
    keyboard.append([InlineKeyboardButton("🏠 Menú Principal", callback_data=home_callback)])
    return InlineKeyboardMarkup(keyboard)


def get_location_detail_keyboard(back_callback: str, home_callback: str) -> InlineKeyboardMarkup:
    """Teclado para la vista detallada de una ubicación."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔙 Volver", callback_data=back_callback),
                InlineKeyboardButton("🏠 Menú Principal", callback_data=home_callback),
            ]
        ]
    )


# --- Teclados para el ADMIN ---
async def get_locations_for_action_keyboard(bot_id: int, action: str):
    """Muestra la lista de Ubicaciones para que el admin las modifique o elimine."""
    items = await content_db.get_all_items(bot_id, 'locations', 'name')
    if not items:
        return None

    emoji = "✏️" if action == "modify" else "🗑️"
    keyboard = [
        [
            InlineKeyboardButton(
                f"{emoji} {item['title']}", callback_data=f"loc_{action}_{item['id']}"
            )
        ]
        for item in items
    ]
    keyboard.append([InlineKeyboardButton("🔙 Volver", callback_data="locations_admin_hub")])
    return InlineKeyboardMarkup(keyboard)


async def get_locations_reorder_keyboard(bot_id: int):
    """Muestra la lista de Ubicaciones con botones para reordenar."""
    items = await content_db.get_all_items(bot_id, 'locations', 'name')
    if not items or len(items) < 2:
        return None

    keyboard = []
    for index, item in enumerate(items):
        row = [InlineKeyboardButton(item['title'], callback_data="ignore")]
        if index > 0:
            row.append(InlineKeyboardButton("🔼", callback_data=f"loc_reorder_up_{item['id']}"))
        if index < len(items) - 1:
            row.append(InlineKeyboardButton("🔽", callback_data=f"loc_reorder_down_{item['id']}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("✅ Listo", callback_data="locations_admin_hub")])
    return InlineKeyboardMarkup(keyboard)