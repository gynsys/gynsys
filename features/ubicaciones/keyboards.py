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


def get_days_selection_keyboard(selected_days: list, confirm_callback: str):
    """
    Genera un teclado para seleccionar días de la semana.
    selected_days: Lista de enteros (0=Lunes, 6=Domingo).
    """
    days = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    keyboard = []
    row = []
    for i, day_name in enumerate(days):
        # Si el día está seleccionado, ponemos un check
        text = f"✅ {day_name}" if i in selected_days else day_name
        callback_data = f"loc_toggle_day_{i}"
        row.append(InlineKeyboardButton(text, callback_data=callback_data))
        
        # Max 3 botones por fila
        if len(row) == 3:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
        
    # Botón de confirmar
    keyboard.append([InlineKeyboardButton("✅ Continuar", callback_data=confirm_callback)])
    
    return InlineKeyboardMarkup(keyboard)

