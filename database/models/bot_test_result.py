"""
Modelo para almacenar los resultados del test de endometriosis.
"""
from sqlalchemy import Column, Integer, String, Float
from .base import Base

class BotTestResult(Base):
    """
    Modelo para almacenar los resultados de los tests realizados por los usuarios.
    Permite calcular estadísticas (total de tests, distribución de resultados).
    """
    __tablename__ = 'bot_test_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    bot_id = Column(Integer, nullable=False, index=True)
    score = Column(Integer, nullable=False)  # Puntuación obtenida (ej: 6)
    total_questions = Column(Integer, nullable=False) # Total preguntas (ej: 10)
    result_level = Column(String, nullable=False) # Ej: "ALTA PROBABILIDAD"
    timestamp = Column(Integer, nullable=False) # Unix timestamp
    
    def __repr__(self):
        return f"<BotTestResult(user={self.user_id}, score={self.score}/{self.total_questions}, level='{self.result_level}')>"
