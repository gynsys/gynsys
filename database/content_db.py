"""
Base de datos para gestión de contenido genérico

⚠️ DEPRECATED: Este módulo está siendo migrado a SQLAlchemy.
Usa database.repositories.content_repository en código nuevo.

Este archivo mantiene compatibilidad durante la migración.
"""
import logging
from typing import Optional
from database.session import get_session
from database.repositories.content_repository import TextContentRepository, GenericContentRepository

logger = logging.getLogger(__name__)


# Funciones de compatibilidad para text_content
async def delete_content_by_key(bot_id: int, key: str) -> bool:
    """Elimina una entrada de text_content por su clave."""
    async with get_session() as session:
        repo = TextContentRepository(session)
        return await repo.delete_content_by_key(bot_id, key)


async def get_next_custom_text_id(bot_id: int) -> int:
    """Busca la clave de texto personalizada más alta y devuelve el siguiente número disponible."""
    async with get_session() as session:
        repo = TextContentRepository(session)
        return await repo.get_next_custom_text_id(bot_id)


async def get_all_items(bot_id: int, table_name: str, title_column: str):
    """Obtiene todos los items de una tabla específica."""
    async with get_session() as session:
        repo = GenericContentRepository(session)
        return await repo.get_all_items(bot_id, table_name, title_column)


async def get_item_details(item_id: int, table_name: str, title_column: str, content_column: str | None):
    """Obtiene los detalles de un item específico."""
    async with get_session() as session:
        repo = GenericContentRepository(session)
        return await repo.get_item_details(item_id, table_name, title_column, content_column)


async def add_item(bot_id: int, table_name: str, title: str, content: str | None, title_column: str, content_column: str | None):
    """Añade un nuevo item a una tabla."""
    async with get_session() as session:
        repo = GenericContentRepository(session)
        return await repo.add_item(bot_id, table_name, title, content, title_column, content_column)


async def update_item(item_id: int, table_name: str, title: str, content: str | None, title_column: str, content_column: str | None) -> bool:
    """Actualiza un item existente."""
    async with get_session() as session:
        repo = GenericContentRepository(session)
        return await repo.update_item(item_id, table_name, title, content, title_column, content_column)


async def delete_item(item_id: int, table_name: str) -> bool:
    """Elimina un item de una tabla."""
    async with get_session() as session:
        repo = GenericContentRepository(session)
        return await repo.delete_item(item_id, table_name)


async def reorder_item(bot_id: int, table_name: str, item_id: int, direction: str) -> bool:
    """Reordena un item moviéndolo arriba o abajo."""
    async with get_session() as session:
        repo = GenericContentRepository(session)
        return await repo.reorder_item(bot_id, table_name, item_id, direction)


async def get_content(key: str, bot_id: int):
    """Obtiene el contenido de una clave específica."""
    async with get_session() as session:
        repo = TextContentRepository(session)
        return await repo.get_content(key, bot_id)


async def update_content(key: str, value: str, bot_id: int):
    """Actualiza o inserta contenido en text_content."""
    async with get_session() as session:
        repo = TextContentRepository(session)
        return await repo.update_content(key, value, bot_id)


async def get_item_content(item_id: int, content_column: str, table_name: str):
    """Obtiene solo la columna de contenido de un item específico."""
    async with get_session() as session:
        repo = GenericContentRepository(session)
        return await repo.get_item_content(item_id, content_column, table_name)


async def get_submenu_headers(bot_id: int):
    """Obtiene todas las entradas de text_content que son encabezados de submenús."""
    async with get_session() as session:
        repo = TextContentRepository(session)
        return await repo.get_submenu_headers(bot_id)


async def get_item_details_with_media(item_id: int, table_name: str, title_column: str, content_column: str):
    """Obtiene todos los detalles de un item, incluyendo el tipo y file_id del media."""
    async with get_session() as session:
        repo = GenericContentRepository(session)
        return await repo.get_item_details_with_media(item_id, table_name, title_column, content_column)


async def update_item_with_media(item_id: int, table_name: str, title: str, content: str, media_file_id: str | None, media_type: str | None, title_column: str, content_column: str) -> bool:
    """Actualiza un item que contiene un media (foto o video)."""
    async with get_session() as session:
        repo = GenericContentRepository(session)
        return await repo.update_item_with_media(item_id, table_name, title, content, media_file_id, media_type, title_column, content_column)


async def add_item_with_media(bot_id: int, table_name: str, title: str, content: str, media_file_id: str, media_type: str, title_column: str, content_column: str):
    """Añade un nuevo item que contiene un media (foto o video)."""
    async with get_session() as session:
        repo = GenericContentRepository(session)
        return await repo.add_item_with_media(bot_id, table_name, title, content, media_file_id, media_type, title_column, content_column)
