# common/keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_return_to_main_menu_keyboard(from_media: bool = False) -> InlineKeyboardMarkup:
    main_menu_cb = "main_menu_from_media" if from_media else "main_menu"
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Menú Principal", callback_data=main_menu_cb)]])

def get_back_to_menu_keyboard(back_callback: str, from_media: bool = False) -> InlineKeyboardMarkup:
    main_menu_cb = "main_menu_from_media" if from_media else "main_menu"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Volver", callback_data=back_callback),
            InlineKeyboardButton("🏠 Menú Principal", callback_data=main_menu_cb)
        ]
    ])

def get_back_to_submenu_keyboard(submenu_id: int, from_media: bool = False) -> InlineKeyboardMarkup:
    main_menu_cb = "main_menu_from_media" if from_media else "main_menu"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Volver", callback_data=f"open_submenu_{submenu_id}"),
            InlineKeyboardButton("🏠 Menú Principal", callback_data=main_menu_cb)
        ]
    ])

# --- ¡FUNCIÓN AÑADIDA! ---
def get_delete_confirmation_keyboard(item_type_callback: str, back_callback: str) -> InlineKeyboardMarkup:
    """
    Genera un teclado de confirmación universal para operaciones de borrado.
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Sí, eliminar", callback_data=item_type_callback),
            InlineKeyboardButton("❌ No, cancelar", callback_data=back_callback)
        ]
    ])

def get_cancel_button_keyboard() -> InlineKeyboardMarkup:
    """
    Genera un teclado simple con un único botón para cancelar una conversación.
    """
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancelar", callback_data="cancel_conv")]])