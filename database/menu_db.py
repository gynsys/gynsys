# database/menu_db.py
"""
Capa de compatibilidad para menu_db.py.
Migrado a SQLAlchemy asíncrono usando MenuRepository.
"""
import asyncio
import logging
from .session import get_session
from .repositories.menu_repository import (
    MainMenuButtonRepository,
    SubmenuRepository,
    SubmenuButtonRepository
)

logger = logging.getLogger(__name__)

# --- MAIN MENU BUTTONS ---

async def get_inactive_main_menu_buttons(bot_id: int):
    """Obtiene TODOS los botones del menú principal que están inactivos."""
    async with get_session() as session:
        repo = MainMenuButtonRepository(session)
        return await repo.get_inactive_main_menu_buttons(bot_id)


async def get_main_menu_buttons(bot_id: int):
    """Obtiene los botones activos del menú principal."""
    async with get_session() as session:
        repo = MainMenuButtonRepository(session)
        return await repo.get_main_menu_buttons(bot_id)


async def get_main_menu_button_details(button_id: int):
    """Obtiene los detalles completos de un botón."""
    async with get_session() as session:
        repo = MainMenuButtonRepository(session)
        return await repo.get_main_menu_button_details(button_id)


async def add_main_menu_button(bot_id: int, text: str, callback_data: str, row_number: int) -> bool:
    """Añade un botón al menú principal."""
    async with get_session() as session:
        repo = MainMenuButtonRepository(session)
        return await repo.add_main_menu_button(bot_id, text, callback_data, row_number)


async def delete_main_menu_button(button_id: int) -> bool:
    """Elimina un botón del menú principal."""
    async with get_session() as session:
        repo = MainMenuButtonRepository(session)
        return await repo.delete_main_menu_button(button_id)


async def deactivate_main_menu_button(button_id: int) -> bool:
    """En lugar de borrar, marca un botón como inactivo."""
    async with get_session() as session:
        repo = MainMenuButtonRepository(session)
        return await repo.deactivate_main_menu_button(button_id)


async def get_inactive_core_modules(bot_id: int):
    """
    Obtiene los botones de módulos principales que han sido 'eliminados' (están inactivos).
    """
    async with get_session() as session:
        repo = MainMenuButtonRepository(session)
        # Importar CORE_MODULES_CALLBACKS desde el módulo original
        try:
            from features.main_menu.admin_handlers import CORE_MODULES_CALLBACKS
            return await repo.get_inactive_core_modules(bot_id, CORE_MODULES_CALLBACKS)
        except ImportError:
            logger.warning("No se pudo importar CORE_MODULES_CALLBACKS, retornando lista vacía")
            return []


async def reactivate_main_menu_button(button_id: int) -> bool:
    """Marca un botón como activo de nuevo."""
    async with get_session() as session:
        repo = MainMenuButtonRepository(session)
        return await repo.reactivate_main_menu_button(button_id)


# --- SUBMENUS ---

async def create_submenu(bot_id: int, name: str) -> int | None:
    """Crea un nuevo submenú."""
    async with get_session() as session:
        repo = SubmenuRepository(session)
        return await repo.create_submenu(bot_id, name)


async def get_all_submenus(bot_id: int):
    """Obtiene todos los submenús activos."""
    async with get_session() as session:
        repo = SubmenuRepository(session)
        return await repo.get_all_submenus(bot_id)


async def get_submenu_details(submenu_id: int):
    """Obtiene los detalles completos de un submenú."""
    async with get_session() as session:
        repo = SubmenuRepository(session)
        return await repo.get_submenu_details(submenu_id)


async def delete_submenu(submenu_id: int) -> bool:
    """Elimina un submenú."""
    async with get_session() as session:
        repo = SubmenuRepository(session)
        return await repo.delete_submenu(submenu_id)


# --- SUBMENU BUTTONS ---

async def get_submenu_buttons(submenu_id: int):
    """Obtiene los botones activos de un submenú."""
    async with get_session() as session:
        repo = SubmenuButtonRepository(session)
        return await repo.get_submenu_buttons(submenu_id)


async def get_submenu_button_details(button_id: int):
    """Obtiene los detalles completos de un botón de submenú."""
    async with get_session() as session:
        repo = SubmenuButtonRepository(session)
        return await repo.get_submenu_button_details(button_id)


async def add_submenu_button(submenu_id: int, text: str, callback_data: str, row_number: int) -> bool:
    """Añade un botón a un submenú."""
    async with get_session() as session:
        repo = SubmenuButtonRepository(session)
        return await repo.add_submenu_button(submenu_id, text, callback_data, row_number)


async def delete_submenu_button(button_id: int) -> bool:
    """Elimina un botón de submenú."""
    async with get_session() as session:
        repo = SubmenuButtonRepository(session)
        return await repo.delete_submenu_button(button_id)


async def reorder_submenu_button(submenu_id: int, button_id: int, direction: str) -> bool:
    """Reordena un botón de submenú."""
    async with get_session() as session:
        repo = SubmenuButtonRepository(session)
        return await repo.reorder_submenu_button(submenu_id, button_id, direction)


async def update_submenu_button_text(button_id: int, new_text: str) -> bool:
    """Actualiza solo el texto de un botón de submenú."""
    async with get_session() as session:
        repo = SubmenuButtonRepository(session)
        return await repo.update_submenu_button_text(button_id, new_text)
