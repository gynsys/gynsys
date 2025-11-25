"""
Repository para gestión de contenido genérico (FAQs, Gallery, Precios, etc.).
Reemplaza content_db.py con SQLAlchemy asíncrono.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, text
from sqlalchemy.orm import selectinload
from database.models.content import TextContent, FAQ, Gallery, Precio
from database.repositories.base_repository import BaseRepository
from database.sql_utils import validate_column_or_table_name
import logging

logger = logging.getLogger(__name__)


class TextContentRepository(BaseRepository[TextContent]):
    """
    Repository para operaciones con text_content.
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(TextContent, session)
    
    async def get_content(self, key: str, bot_id: int) -> Optional[str]:
        """
        Obtiene el contenido de una clave específica.
        
        Args:
            key: Clave del contenido
            bot_id: ID del bot
        
        Returns:
            Valor del contenido o None si no existe
        """
        result = await self.session.execute(
            select(TextContent.value).where(
                TextContent.key == key,
                TextContent.bot_id == bot_id
            )
        )
        row = result.first()
        return row[0] if row else None
    
    async def update_content(self, key: str, value: str, bot_id: int) -> bool:
        """
        Actualiza o inserta contenido en text_content.
        IMPORTANTE: Elimina cualquier registro existente antes de insertar para evitar duplicados.
        
        Args:
            key: Clave del contenido
            value: Valor del contenido
            bot_id: ID del bot
        
        Returns:
            True si se actualizó correctamente
        """
        try:
            # Primero eliminar cualquier registro existente
            await self.session.execute(
                delete(TextContent).where(
                    TextContent.key == key,
                    TextContent.bot_id == bot_id
                )
            )
            
            # Luego insertar el nuevo valor
            new_content = TextContent(
                key=key,
                value=value,
                bot_id=bot_id
            )
            self.session.add(new_content)
            await self.session.flush()
            
            logger.info(f"✅ Contenido actualizado: key={key}, bot_id={bot_id}, value_length={len(value)}")
            return True
        except Exception as e:
            logger.error(f"❌ Error al actualizar contenido: key={key}, bot_id={bot_id}, error={e}", exc_info=True)
            await self.session.rollback()
            return False
    
    async def delete_content_by_key(self, bot_id: int, key: str) -> bool:
        """
        Elimina una entrada de text_content por su clave.
        
        Args:
            bot_id: ID del bot
            key: Clave del contenido
        
        Returns:
            True si se eliminó, False si no existía
        """
        result = await self.session.execute(
            delete(TextContent).where(
                TextContent.bot_id == bot_id,
                TextContent.key == key
            )
        )
        await self.session.flush()
        return result.rowcount > 0
    
    async def get_next_custom_text_id(self, bot_id: int) -> int:
        """
        Busca la clave de texto personalizada más alta (ej: 'custom_text_5')
        y devuelve el siguiente número disponible.
        
        Args:
            bot_id: ID del bot
        
        Returns:
            Siguiente ID disponible
        """
        result = await self.session.execute(
            select(TextContent.key).where(
                TextContent.bot_id == bot_id,
                TextContent.key.like('custom_text_%')
            )
        )
        rows = result.all()
        
        max_id = 0
        for row in rows:
            try:
                num = int(row[0].replace('custom_text_', ''))
                if num > max_id:
                    max_id = num
            except (ValueError, TypeError):
                continue
        
        return max_id + 1
    
    async def get_submenu_headers(self, bot_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las entradas de text_content que son encabezados de submenús.
        
        Args:
            bot_id: ID del bot
        
        Returns:
            Lista de diccionarios con key y value
        """
        result = await self.session.execute(
            select(TextContent.key, TextContent.value)
            .where(
                TextContent.bot_id == bot_id,
                TextContent.key.like('header_submenu_%')
            )
            .order_by(TextContent.key)
        )
        return [{'key': row[0], 'value': row[1]} for row in result.all()]


class GenericContentRepository:
    """
    Repository genérico para operaciones con tablas dinámicas (faqs, gallery, precios, etc.).
    Valida nombres de tabla/columna antes de ejecutar queries.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_all_items(self, bot_id: int, table_name: str, title_column: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los items de una tabla específica.
        
        Args:
            bot_id: ID del bot
            table_name: Nombre de la tabla (debe ser validado)
            title_column: Nombre de la columna de título (debe ser validado)
        
        Returns:
            Lista de diccionarios con id y title
        """
        # Validar nombres
        if not validate_column_or_table_name(table_name) or not validate_column_or_table_name(title_column):
            logger.error(f"Nombres inválidos: table={table_name}, column={title_column}")
            return []
        
        try:
            # Usar text() para construir query dinámico de forma segura
            query = text(f"""
                SELECT id, {title_column} as title 
                FROM {table_name} 
                WHERE bot_id = :bot_id 
                ORDER BY display_order, {title_column}
            """)
            result = await self.session.execute(query, {'bot_id': bot_id})
            return [{'id': row[0], 'title': row[1]} for row in result.all()]
        except Exception as e:
            logger.error(f"Error en get_all_items: {e}")
            return []
    
    async def get_item_details(
        self, 
        item_id: int, 
        table_name: str, 
        title_column: str, 
        content_column: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene los detalles de un item específico.
        
        Args:
            item_id: ID del item
            table_name: Nombre de la tabla
            title_column: Nombre de la columna de título
            content_column: Nombre de la columna de contenido (opcional)
        
        Returns:
            Diccionario con title y content, o None si no existe
        """
        # Validar nombres
        if not validate_column_or_table_name(table_name) or not validate_column_or_table_name(title_column):
            logger.error(f"Nombres inválidos: table={table_name}, title_column={title_column}")
            return None
        if content_column and not validate_column_or_table_name(content_column):
            logger.error(f"Nombre de columna de contenido inválido: {content_column}")
            return None
        
        try:
            content_col = content_column if content_column else title_column
            query = text(f"""
                SELECT {title_column} as title, {content_col} as content 
                FROM {table_name} 
                WHERE id = :item_id
            """)
            result = await self.session.execute(query, {'item_id': item_id})
            row = result.first()
            if row:
                # Convertir Row a diccionario correctamente
                if hasattr(row, '_mapping'):
                    return dict(row._mapping)
                else:
                    # Fallback: construir diccionario manualmente
                    return {'title': row[0], 'content': row[1]}
            return None
        except Exception as e:
            logger.error(f"Error en get_item_details: {e}")
            return None
    
    async def add_item(
        self, 
        bot_id: int, 
        table_name: str, 
        title: str, 
        content: Optional[str], 
        title_column: str, 
        content_column: Optional[str] = None
    ) -> bool:
        """
        Añade un nuevo item a una tabla.
        
        Args:
            bot_id: ID del bot
            table_name: Nombre de la tabla
            title: Título del item
            content: Contenido del item (opcional)
            title_column: Nombre de la columna de título
            content_column: Nombre de la columna de contenido (opcional)
        
        Returns:
            True si se añadió correctamente
        """
        # Validar nombres
        if not validate_column_or_table_name(table_name) or not validate_column_or_table_name(title_column):
            logger.error(f"Nombres inválidos: table={table_name}, title_column={title_column}")
            return False
        if content_column and not validate_column_or_table_name(content_column):
            logger.error(f"Nombre de columna de contenido inválido: {content_column}")
            return False
        
        try:
            # Obtener max display_order
            max_order_query = text(f"SELECT MAX(display_order) as max_order FROM {table_name} WHERE bot_id = :bot_id")
            result = await self.session.execute(max_order_query, {'bot_id': bot_id})
            row = result.first()
            max_order = row[0] if row and row[0] is not None else 0
            
            # Insertar item
            if content_column and content is not None:
                insert_query = text(f"""
                    INSERT INTO {table_name} (bot_id, {title_column}, {content_column}, display_order) 
                    VALUES (:bot_id, :title, :content, :display_order)
                """)
                await self.session.execute(insert_query, {
                    'bot_id': bot_id,
                    'title': title,
                    'content': content,
                    'display_order': max_order + 1
                })
            else:
                insert_query = text(f"""
                    INSERT INTO {table_name} (bot_id, {title_column}, display_order) 
                    VALUES (:bot_id, :title, :display_order)
                """)
                await self.session.execute(insert_query, {
                    'bot_id': bot_id,
                    'title': title,
                    'display_order': max_order + 1
                })
            
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error en add_item: {e}")
            await self.session.rollback()
            return False
    
    async def update_item(
        self, 
        item_id: int, 
        table_name: str, 
        title: str, 
        content: Optional[str], 
        title_column: str, 
        content_column: Optional[str] = None
    ) -> bool:
        """
        Actualiza un item existente.
        
        Args:
            item_id: ID del item
            table_name: Nombre de la tabla
            title: Nuevo título
            content: Nuevo contenido (opcional)
            title_column: Nombre de la columna de título
            content_column: Nombre de la columna de contenido (opcional)
        
        Returns:
            True si se actualizó correctamente
        """
        # Validar nombres
        if not validate_column_or_table_name(table_name) or not validate_column_or_table_name(title_column):
            logger.error(f"Nombres inválidos: table={table_name}, title_column={title_column}")
            return False
        if content_column and not validate_column_or_table_name(content_column):
            logger.error(f"Nombre de columna de contenido inválido: {content_column}")
            return False
        
        try:
            if content_column and content is not None:
                update_query = text(f"""
                    UPDATE {table_name} 
                    SET {title_column} = :title, {content_column} = :content 
                    WHERE id = :item_id
                """)
                result = await self.session.execute(update_query, {
                    'title': title,
                    'content': content,
                    'item_id': item_id
                })
            else:
                update_query = text(f"""
                    UPDATE {table_name} 
                    SET {title_column} = :title 
                    WHERE id = :item_id
                """)
                result = await self.session.execute(update_query, {
                    'title': title,
                    'item_id': item_id
                })
            
            await self.session.flush()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error en update_item: {e}")
            await self.session.rollback()
            return False
    
    async def delete_item(self, item_id: int, table_name: str) -> bool:
        """
        Elimina un item de una tabla.
        
        Args:
            item_id: ID del item
            table_name: Nombre de la tabla
        
        Returns:
            True si se eliminó correctamente
        """
        # Validar nombre de tabla
        if not validate_column_or_table_name(table_name):
            logger.error(f"Nombre de tabla inválido: {table_name}")
            return False
        
        try:
            delete_query = text(f"DELETE FROM {table_name} WHERE id = :item_id")
            result = await self.session.execute(delete_query, {'item_id': item_id})
            await self.session.flush()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error en delete_item: {e}")
            await self.session.rollback()
            return False
    
    async def reorder_item(self, bot_id: int, table_name: str, item_id: int, direction: str) -> bool:
        """
        Reordena un item moviéndolo arriba o abajo.
        
        Args:
            bot_id: ID del bot
            table_name: Nombre de la tabla
            item_id: ID del item a mover
            direction: 'up' o 'down'
        
        Returns:
            True si se reordenó correctamente
        """
        # Validar nombre de tabla
        if not validate_column_or_table_name(table_name):
            logger.error(f"Nombre de tabla inválido: {table_name}")
            return False
        
        try:
            # Obtener todos los items ordenados
            select_query = text(f"SELECT id, display_order FROM {table_name} WHERE bot_id = :bot_id ORDER BY display_order")
            result = await self.session.execute(select_query, {'bot_id': bot_id})
            items = result.all()
            
            item_ids = [item[0] for item in items]
            if item_id not in item_ids:
                return False
            
            current_index = item_ids.index(item_id)
            
            if direction == 'up' and current_index > 0:
                swap_with_index = current_index - 1
            elif direction == 'down' and current_index < len(items) - 1:
                swap_with_index = current_index + 1
            else:
                return False
            
            # Intercambiar display_order
            item_to_move = items[current_index]
            item_to_swap_with = items[swap_with_index]
            
            update1_query = text(f"UPDATE {table_name} SET display_order = :order WHERE id = :item_id")
            update2_query = text(f"UPDATE {table_name} SET display_order = :order WHERE id = :item_id")
            
            await self.session.execute(update1_query, {
                'order': item_to_swap_with[1],
                'item_id': item_to_move[0]
            })
            await self.session.execute(update2_query, {
                'order': item_to_move[1],
                'item_id': item_to_swap_with[0]
            })
            
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error al reordenar en {table_name}: {e}")
            await self.session.rollback()
            return False
    
    async def get_item_content(self, item_id: int, content_column: str, table_name: str) -> Optional[str]:
        """
        Obtiene solo la columna de contenido de un item específico.
        
        Args:
            item_id: ID del item
            content_column: Nombre de la columna de contenido
            table_name: Nombre de la tabla
        
        Returns:
            Contenido del item o None
        """
        # Validar nombres
        if not validate_column_or_table_name(table_name) or not validate_column_or_table_name(content_column):
            logger.error(f"Nombres inválidos: table={table_name}, column={content_column}")
            return None
        
        try:
            query = text(f"SELECT {content_column} as content FROM {table_name} WHERE id = :item_id")
            result = await self.session.execute(query, {'item_id': item_id})
            row = result.first()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Error en get_item_content: {e}")
            return None
    
    async def get_item_details_with_media(
        self, 
        item_id: int, 
        table_name: str, 
        title_column: str, 
        content_column: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene todos los detalles de un item, incluyendo el tipo y file_id del media.
        
        Args:
            item_id: ID del item
            table_name: Nombre de la tabla
            title_column: Nombre de la columna de título
            content_column: Nombre de la columna de contenido
        
        Returns:
            Diccionario con detalles del item incluyendo media, o None
        """
        # Validar nombres
        if not all(validate_column_or_table_name(name) for name in [table_name, title_column, content_column]):
            logger.error(f"Nombres inválidos: table={table_name}, title={title_column}, content={content_column}")
            return None
        
        try:
            query = text(f"""
                SELECT id, {title_column} as title, {content_column} as content, media_file_id, media_type 
                FROM {table_name} 
                WHERE id = :item_id
            """)
            result = await self.session.execute(query, {'item_id': item_id})
            row = result.first()
            if row:
                # Convertir Row a dict correctamente
                # En SQLAlchemy 2.0+, Row tiene _mapping que es un dict-like object
                if hasattr(row, '_mapping'):
                    return dict(row._mapping)
                # Fallback: construir dict manualmente
                return {
                    'id': row.id,
                    'title': getattr(row, 'title', None),
                    'content': getattr(row, 'content', None),
                    'media_file_id': getattr(row, 'media_file_id', None),
                    'media_type': getattr(row, 'media_type', None)
                }
            return None
        except Exception as e:
            logger.error(f"Error en get_item_details_with_media: {e}", exc_info=True)
            return None
    
    async def update_item_with_media(
        self, 
        item_id: int, 
        table_name: str, 
        title: str, 
        content: str, 
        media_file_id: Optional[str], 
        media_type: Optional[str], 
        title_column: str, 
        content_column: str
    ) -> bool:
        """
        Actualiza un item que contiene un media (foto o video).
        
        Args:
            item_id: ID del item
            table_name: Nombre de la tabla
            title: Nuevo título
            content: Nuevo contenido
            media_file_id: File ID del media (opcional)
            media_type: Tipo del media (opcional)
            title_column: Nombre de la columna de título
            content_column: Nombre de la columna de contenido
        
        Returns:
            True si se actualizó correctamente
        """
        # Validar nombres
        if not all(validate_column_or_table_name(name) for name in [table_name, title_column, content_column]):
            logger.error(f"Nombres inválidos: table={table_name}, title={title_column}, content={content_column}")
            return False
        
        try:
            query = text(f"""
                UPDATE {table_name} 
                SET {title_column} = :title, {content_column} = :content, 
                    media_file_id = :media_file_id, media_type = :media_type 
                WHERE id = :item_id
            """)
            result = await self.session.execute(query, {
                'title': title,
                'content': content,
                'media_file_id': media_file_id,
                'media_type': media_type,
                'item_id': item_id
            })
            await self.session.flush()
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error en update_item_with_media: {e}")
            await self.session.rollback()
            return False
    
    async def add_item_with_media(
        self, 
        bot_id: int, 
        table_name: str, 
        title: str, 
        content: str, 
        media_file_id: str, 
        media_type: str, 
        title_column: str, 
        content_column: str
    ) -> bool:
        """
        Añade un nuevo item que contiene un media (foto o video).
        
        Args:
            bot_id: ID del bot
            table_name: Nombre de la tabla
            title: Título del item
            content: Contenido del item
            media_file_id: File ID del media
            media_type: Tipo del media
            title_column: Nombre de la columna de título
            content_column: Nombre de la columna de contenido
        
        Returns:
            True si se añadió correctamente
        """
        # Validar nombres
        if not all(validate_column_or_table_name(name) for name in [table_name, title_column, content_column]):
            logger.error(f"Nombres inválidos: table={table_name}, title={title_column}, content={content_column}")
            return False
        
        try:
            # Obtener max display_order
            max_order_query = text(f"SELECT MAX(display_order) as max_order FROM {table_name} WHERE bot_id = :bot_id")
            result = await self.session.execute(max_order_query, {'bot_id': bot_id})
            row = result.first()
            max_order = row[0] if row and row[0] is not None else -1
            
            # Insertar item
            insert_query = text(f"""
                INSERT INTO {table_name} (bot_id, {title_column}, {content_column}, media_file_id, media_type, display_order) 
                VALUES (:bot_id, :title, :content, :media_file_id, :media_type, :display_order)
            """)
            await self.session.execute(insert_query, {
                'bot_id': bot_id,
                'title': title,
                'content': content,
                'media_file_id': media_file_id,
                'media_type': media_type,
                'display_order': max_order + 1
            })
            
            await self.session.flush()
            return True
        except Exception as e:
            logger.error(f"Error en add_item_with_media: {e}")
            await self.session.rollback()
            return False

