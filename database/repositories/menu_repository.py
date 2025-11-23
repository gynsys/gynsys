"""
Repository para gestionar menús y botones de menú.
Reemplaza menu_db.py con SQLAlchemy asíncrono.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from .base_repository import BaseRepository
from database.models.menu import MainMenuButton, Submenu, SubmenuButton
import logging

logger = logging.getLogger(__name__)


# --- MAIN MENU BUTTONS ---

class MainMenuButtonRepository(BaseRepository[MainMenuButton]):
    """Repository para botones del menú principal."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(MainMenuButton, session)
    
    async def get_inactive_main_menu_buttons(self, bot_id: int) -> List[Dict[str, Any]]:
        """Obtiene TODOS los botones del menú principal que están inactivos."""
        try:
            stmt = select(MainMenuButton).where(
                MainMenuButton.bot_id == bot_id,
                MainMenuButton.is_active == False
            ).order_by(MainMenuButton.row_number, MainMenuButton.display_order)
            
            result = await self.session.execute(stmt)
            buttons = result.scalars().all()
            
            return [{'id': b.id, 'text': b.text} for b in buttons]
        except Exception as e:
            logger.error(f"Error al obtener botones inactivos: {e}")
            return []
    
    async def get_main_menu_buttons(self, bot_id: int) -> List[Dict[str, Any]]:
        """Obtiene los botones activos del menú principal."""
        try:
            stmt = select(MainMenuButton).where(
                MainMenuButton.bot_id == bot_id,
                MainMenuButton.is_active == True
            ).order_by(MainMenuButton.row_number, MainMenuButton.display_order)
            
            result = await self.session.execute(stmt)
            buttons = result.scalars().all()
            
            return [
                {
                    'id': b.id,
                    'text': b.text,
                    'callback_data': b.callback_data,
                    'row_number': b.row_number,
                    'display_order': b.display_order
                }
                for b in buttons
            ]
        except Exception as e:
            logger.error(f"Error al obtener botones del menú principal: {e}")
            return []
    
    async def get_main_menu_button_details(self, button_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene los detalles completos de un botón."""
        try:
            button = await self.get_by_id(button_id)
            if button:
                return {
                    'id': button.id,
                    'bot_id': button.bot_id,
                    'text': button.text,
                    'callback_data': button.callback_data,
                    'row_number': button.row_number,
                    'display_order': button.display_order,
                    'is_active': button.is_active
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener detalles del botón: {e}")
            return None
    
    async def add_main_menu_button(
        self,
        bot_id: int,
        text: str,
        callback_data: str,
        row_number: int
    ) -> bool:
        """Añade un botón al menú principal."""
        try:
            # Obtener el máximo display_order para esta fila
            stmt = select(func.max(MainMenuButton.display_order)).where(
                MainMenuButton.bot_id == bot_id,
                MainMenuButton.row_number == row_number
            )
            result = await self.session.execute(stmt)
            max_order = result.scalar() or -1
            
            button = MainMenuButton(
                bot_id=bot_id,
                text=text,
                callback_data=callback_data,
                row_number=row_number,
                display_order=max_order + 1,
                is_active=True
            )
            self.session.add(button)
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error al añadir botón al menú principal: {e}")
            await self.session.rollback()
            return False
    
    async def delete_main_menu_button(self, button_id: int) -> bool:
        """Elimina un botón del menú principal."""
        try:
            button = await self.get_by_id(button_id)
            if not button:
                return False
            
            # Si es un botón de contenido personalizado, eliminar también el contenido
            if button.callback_data.startswith('show_content_custom_text_'):
                content_key = button.callback_data.replace('show_content_', '')
                from .content_repository import TextContentRepository
                content_repo = TextContentRepository(self.session)
                await content_repo.delete_content_by_key(button.bot_id, content_key)
            
            await self.delete(button_id)
            return True
        except Exception as e:
            logger.error(f"Error al eliminar botón del menú principal: {e}")
            await self.session.rollback()
            return False
    
    async def deactivate_main_menu_button(self, button_id: int) -> bool:
        """Marca un botón como inactivo."""
        try:
            button = await self.get_by_id(button_id)
            if not button:
                return False
            
            button.is_active = False
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error al desactivar botón: {e}")
            await self.session.rollback()
            return False
    
    async def reactivate_main_menu_button(self, button_id: int) -> bool:
        """Marca un botón como activo de nuevo."""
        try:
            button = await self.get_by_id(button_id)
            if not button:
                return False
            
            button.is_active = True
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error al reactivar botón: {e}")
            await self.session.rollback()
            return False
    
    async def get_inactive_core_modules(self, bot_id: int, core_modules_callbacks: tuple) -> List[Dict[str, Any]]:
        """Obtiene los botones de módulos principales que están inactivos."""
        try:
            stmt = select(MainMenuButton).where(
                MainMenuButton.bot_id == bot_id,
                MainMenuButton.is_active == False,
                MainMenuButton.callback_data.in_(core_modules_callbacks)
            )
            
            result = await self.session.execute(stmt)
            buttons = result.scalars().all()
            
            return [{'id': b.id, 'text': b.text} for b in buttons]
        except Exception as e:
            logger.error(f"Error al obtener módulos inactivos: {e}")
            return []


# --- SUBMENUS ---

class SubmenuRepository(BaseRepository[Submenu]):
    """Repository para submenús."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Submenu, session)
    
    async def create_submenu(self, bot_id: int, name: str) -> Optional[int]:
        """Crea un nuevo submenú."""
        try:
            submenu = Submenu(bot_id=bot_id, name=name, is_active=True)
            self.session.add(submenu)
            await self.session.flush()
            return submenu.id
        except Exception as e:
            logger.error(f"Error al crear submenú: {e}")
            await self.session.rollback()
            return None
    
    async def get_all_submenus(self, bot_id: int) -> List[Dict[str, Any]]:
        """Obtiene todos los submenús activos."""
        try:
            stmt = select(Submenu).where(
                Submenu.bot_id == bot_id,
                Submenu.is_active == True
            ).order_by(Submenu.name)
            
            result = await self.session.execute(stmt)
            submenus = result.scalars().all()
            
            return [{'id': s.id, 'name': s.name} for s in submenus]
        except Exception as e:
            logger.error(f"Error al obtener submenús: {e}")
            return []
    
    async def get_submenu_details(self, submenu_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene los detalles completos de un submenú."""
        try:
            submenu = await self.get_by_id(submenu_id)
            if submenu:
                return {
                    'id': submenu.id,
                    'bot_id': submenu.bot_id,
                    'name': submenu.name,
                    'is_active': submenu.is_active,
                    'display_order': submenu.display_order
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener detalles del submenú: {e}")
            return None
    
    async def delete_submenu(self, submenu_id: int) -> bool:
        """Elimina un submenú (cascade elimina sus botones)."""
        try:
            await self.delete(submenu_id)
            return True
        except Exception as e:
            logger.error(f"Error al eliminar submenú: {e}")
            await self.session.rollback()
            return False


# --- SUBMENU BUTTONS ---

class SubmenuButtonRepository(BaseRepository[SubmenuButton]):
    """Repository para botones de submenús."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(SubmenuButton, session)
    
    async def get_submenu_buttons(self, submenu_id: int) -> List[Dict[str, Any]]:
        """Obtiene los botones activos de un submenú."""
        try:
            stmt = select(SubmenuButton).where(
                SubmenuButton.submenu_id == submenu_id,
                SubmenuButton.is_active == True
            ).order_by(SubmenuButton.row_number, SubmenuButton.display_order)
            
            result = await self.session.execute(stmt)
            buttons = result.scalars().all()
            
            return [
                {
                    'id': b.id,
                    'text': b.text,
                    'callback_data': b.callback_data,
                    'row_number': b.row_number,
                    'display_order': b.display_order
                }
                for b in buttons
            ]
        except Exception as e:
            logger.error(f"Error al obtener botones del submenú: {e}")
            return []
    
    async def get_submenu_button_details(self, button_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene los detalles completos de un botón de submenú."""
        try:
            button = await self.get_by_id(button_id)
            if button:
                return {
                    'id': button.id,
                    'submenu_id': button.submenu_id,
                    'text': button.text,
                    'callback_data': button.callback_data,
                    'row_number': button.row_number,
                    'display_order': button.display_order,
                    'is_active': button.is_active
                }
            return None
        except Exception as e:
            logger.error(f"Error al obtener detalles del botón: {e}")
            return None
    
    async def add_submenu_button(
        self,
        submenu_id: int,
        text: str,
        callback_data: str,
        row_number: int
    ) -> bool:
        """Añade un botón a un submenú."""
        try:
            # Obtener el máximo display_order para esta fila
            stmt = select(func.max(SubmenuButton.display_order)).where(
                SubmenuButton.submenu_id == submenu_id,
                SubmenuButton.row_number == row_number
            )
            result = await self.session.execute(stmt)
            max_order = result.scalar() or -1
            
            button = SubmenuButton(
                submenu_id=submenu_id,
                text=text,
                callback_data=callback_data,
                row_number=row_number,
                display_order=max_order + 1,
                is_active=True
            )
            self.session.add(button)
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error al añadir botón al submenú: {e}")
            await self.session.rollback()
            return False
    
    async def delete_submenu_button(self, button_id: int) -> bool:
        """Elimina un botón de submenú."""
        try:
            button = await self.get_by_id(button_id)
            if not button:
                return False
            
            # Si es un botón de contenido personalizado, eliminar también el contenido
            if button.callback_data.startswith('show_content_custom_text_'):
                content_key = button.callback_data.replace('show_content_', '')
                # Obtener bot_id del submenú
                from .menu_repository import SubmenuRepository
                submenu_repo = SubmenuRepository(self.session)
                submenu = await submenu_repo.get_by_id(button.submenu_id)
                if submenu:
                    from .content_repository import TextContentRepository
                    content_repo = TextContentRepository(self.session)
                    await content_repo.delete_content_by_key(submenu.bot_id, content_key)
            
            await self.delete(button_id)
            return True
        except Exception as e:
            logger.error(f"Error al eliminar botón de submenú: {e}")
            await self.session.rollback()
            return False
    
    async def reorder_submenu_button(self, submenu_id: int, button_id: int, direction: str) -> bool:
        """Reordena un botón de submenú (intercambia row_number)."""
        try:
            # Obtener todos los botones ordenados
            stmt = select(SubmenuButton).where(
                SubmenuButton.submenu_id == submenu_id
            ).order_by(SubmenuButton.row_number, SubmenuButton.display_order)
            
            result = await self.session.execute(stmt)
            buttons = result.scalars().all()
            
            button_ids = [b.id for b in buttons]
            if button_id not in button_ids:
                return False
            
            current_index = button_ids.index(button_id)
            
            if direction == 'up' and current_index > 0:
                swap_index = current_index - 1
            elif direction == 'down' and current_index < len(buttons) - 1:
                swap_index = current_index + 1
            else:
                return False
            
            # Intercambiar row_number
            button_to_move = buttons[current_index]
            button_to_swap = buttons[swap_index]
            
            temp_row = button_to_move.row_number
            button_to_move.row_number = button_to_swap.row_number
            button_to_swap.row_number = temp_row
            
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error al reordenar botón: {e}")
            await self.session.rollback()
            return False
    
    async def update_submenu_button_text(self, button_id: int, new_text: str) -> bool:
        """Actualiza solo el texto de un botón de submenú."""
        try:
            button = await self.get_by_id(button_id)
            if not button:
                return False
            
            button.text = new_text
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error al actualizar texto del botón: {e}")
            await self.session.rollback()
            return False

