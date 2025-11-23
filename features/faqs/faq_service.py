"""
Servicio específico para operaciones con FAQs.
Usa SQLAlchemy directamente para evitar conflictos con funciones genéricas.
"""
import logging
from typing import Optional, Dict, List
from database.session import get_session
from database.models.content import FAQ
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


async def add_faq_direct(bot_id: int, question: str, answer: str) -> Optional[int]:
    """
    Añade una nueva FAQ directamente usando SQLAlchemy.
    
    Args:
        bot_id: ID del bot
        question: Pregunta
        answer: Respuesta
        
    Returns:
        ID de la FAQ creada o None si falla
    """
    try:
        async with get_session() as session:
            # Obtener el máximo display_order
            stmt = select(func.max(FAQ.display_order)).where(FAQ.bot_id == bot_id)
            result = await session.execute(stmt)
            max_order = result.scalar() or 0
            
            # Crear nueva FAQ
            new_faq = FAQ(
                bot_id=bot_id,
                question=question,
                answer=answer,
                display_order=max_order + 1
            )
            session.add(new_faq)
            await session.flush()
            await session.commit()
            
            logger.info(f"✅ FAQ añadida: id={new_faq.id}, bot_id={bot_id}")
            return new_faq.id
    except Exception as e:
        logger.error(f"❌ Error añadiendo FAQ: {e}", exc_info=True)
        return None


async def update_faq_direct(faq_id: int, bot_id: int, question: Optional[str] = None, answer: Optional[str] = None) -> bool:
    """
    Actualiza una FAQ existente directamente usando SQLAlchemy.
    
    Args:
        faq_id: ID de la FAQ
        bot_id: ID del bot (para validación)
        question: Nueva pregunta (opcional)
        answer: Nueva respuesta (opcional)
        
    Returns:
        True si se actualizó correctamente, False en caso contrario
    """
    try:
        async with get_session() as session:
            # Verificar que la FAQ existe y pertenece al bot
            stmt = select(FAQ).where(FAQ.id == faq_id, FAQ.bot_id == bot_id)
            result = await session.execute(stmt)
            faq = result.scalar_one_or_none()
            
            if not faq:
                logger.error(f"❌ FAQ no encontrada: id={faq_id}, bot_id={bot_id}")
                return False
            
            # Actualizar campos si se proporcionaron
            if question is not None:
                faq.question = question
            if answer is not None:
                faq.answer = answer
            
            await session.commit()
            logger.info(f"✅ FAQ actualizada: id={faq_id}, bot_id={bot_id}")
            return True
    except Exception as e:
        logger.error(f"❌ Error actualizando FAQ: {e}", exc_info=True)
        return False


async def get_faq_details_direct(faq_id: int, bot_id: int) -> Optional[Dict[str, any]]:
    """
    Obtiene los detalles de una FAQ directamente usando SQLAlchemy.
    
    Args:
        faq_id: ID de la FAQ
        bot_id: ID del bot (para validación)
        
    Returns:
        Diccionario con 'title' (question) y 'content' (answer) o None si no existe
    """
    try:
        async with get_session() as session:
            stmt = select(FAQ).where(FAQ.id == faq_id, FAQ.bot_id == bot_id)
            result = await session.execute(stmt)
            faq = result.scalar_one_or_none()
            
            if not faq:
                return None
            
            return {
                'title': faq.question,
                'content': faq.answer,
                'id': faq.id
            }
    except Exception as e:
        logger.error(f"❌ Error obteniendo detalles de FAQ: {e}", exc_info=True)
        return None


async def get_all_faqs_for_bot(bot_id: int) -> List[Dict[str, any]]:
    """
    Obtiene todas las FAQs de un bot ordenadas por display_order.
    
    Args:
        bot_id: ID del bot
        
    Returns:
        Lista de diccionarios con 'id', 'question', 'answer'
    """
    try:
        async with get_session() as session:
            stmt = select(FAQ).where(FAQ.bot_id == bot_id).order_by(FAQ.display_order)
            result = await session.execute(stmt)
            faqs = result.scalars().all()
            
            return [
                {
                    'id': faq.id,
                    'question': faq.question,
                    'answer': faq.answer,
                    'display_order': faq.display_order
                }
                for faq in faqs
            ]
    except Exception as e:
        logger.error(f"❌ Error obteniendo FAQs: {e}", exc_info=True)
        return []

