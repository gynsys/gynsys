"""
Repository para gestionar resultados de tests y estadísticas.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from .base_repository import BaseRepository
from database.models.bot_test_result import BotTestResult
import logging

logger = logging.getLogger(__name__)

class TestResultRepository(BaseRepository[BotTestResult]):
    """Repository para resultados de tests."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(BotTestResult, session)
        
    async def save_result(self, user_id: int, bot_id: int, score: int, total_questions: int, result_level: str, timestamp: int) -> BotTestResult | None:
        """Guarda un nuevo resultado de test."""
        try:
            result = BotTestResult(
                user_id=user_id,
                bot_id=bot_id,
                score=score,
                total_questions=total_questions,
                result_level=result_level,
                timestamp=timestamp
            )
            self.session.add(result)
            await self.session.commit()
            return result
        except Exception as e:
            logger.error(f"Error al guardar resultado de test: {e}")
            await self.session.rollback()
            return None

    async def get_total_tests_count(self, bot_id: int) -> int:
        """Obtiene el número total de tests realizados en este bot."""
        try:
            stmt = select(func.count(BotTestResult.id)).where(BotTestResult.bot_id == bot_id)
            result = await self.session.execute(stmt)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error al contar total de tests: {e}")
            return 0

    async def get_result_distribution(self, bot_id: int) -> dict:
        """
        Obtiene la distribución de resultados para un bot.
        Retorna un dict con keys 'ALTA COINCIDENCIA', 'MODERADA COINCIDENCIA', 'BAJA COINCIDENCIA' y sus counts.
        """
        try:
            stmt = select(BotTestResult.result_level, func.count(BotTestResult.id)).where(
                BotTestResult.bot_id == bot_id
            ).group_by(BotTestResult.result_level)
            
            result = await self.session.execute(stmt)
            counts = {row[0]: row[1] for row in result.all()}
            
            # Asegurar que todas las keys existan
            return {
                'ALTA COINCIDENCIA': counts.get('ALTA COINCIDENCIA', 0),
                'MODERADA COINCIDENCIA': counts.get('MODERADA COINCIDENCIA', 0),
                'BAJA COINCIDENCIA': counts.get('BAJA COINCIDENCIA', 0)
            }
        except Exception as e:
            logger.error(f"Error al obtener distribución de resultados: {e}")
            return {
                'ALTA COINCIDENCIA': 0,
                'MODERADA COINCIDENCIA': 0,
                'BAJA COINCIDENCIA': 0
            }
