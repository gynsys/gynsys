"""
Script para poblar automáticamente las preguntas del test de endometriosis.
Pobla las preguntas para todos los bots que no las tengan, copiando desde un bot que las tenga.
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.session import get_session
from database.engine import init_engine, close_engine
from sqlalchemy import select
from database.models.extra import TestQuestion
from database.models.bot import Bot


async def get_questions_from_bot(source_bot_id: int):
    """Obtiene las preguntas de un bot existente"""
    async with get_session() as session:
        stmt = select(TestQuestion).where(TestQuestion.bot_id == source_bot_id).order_by(TestQuestion.display_order)
        result = await session.execute(stmt)
        questions = result.scalars().all()
        return [
            {
                "question": q.question,
                "display_order": q.display_order
            }
            for q in questions
        ]


async def populate_test_questions(bot_id: int, questions: list, overwrite: bool = False):
    """
    Pobla las preguntas del test para un bot específico.
    
    Args:
        bot_id: ID del bot al que se le agregarán las preguntas
        questions: Lista de preguntas a agregar
        overwrite: Si True, elimina las preguntas existentes antes de agregar
    """
    async with get_session() as session:
        # Verificar si el bot existe
        stmt_bot = select(Bot).where(Bot.id == bot_id)
        result_bot = await session.execute(stmt_bot)
        bot = result_bot.scalar_one_or_none()
        
        if not bot:
            print(f"❌ Error: No se encontró el bot con ID {bot_id}")
            return False
        
        # Verificar si ya existen preguntas
        stmt_existing = select(TestQuestion).where(TestQuestion.bot_id == bot_id)
        result_existing = await session.execute(stmt_existing)
        existing_questions = result_existing.scalars().all()
        
        if existing_questions:
            if overwrite:
                print(f"   ⚠️ Eliminando {len(existing_questions)} preguntas existentes para Bot ID: {bot_id}")
                for q in existing_questions:
                    await session.delete(q)
                await session.commit()
            else:
                print(f"   ⏭️ Bot ID {bot_id} ({bot.doctor_name}) ya tiene {len(existing_questions)} preguntas, omitiendo")
                return True
        
        # Agregar nuevas preguntas
        added_count = 0
        for q_data in questions:
            new_question = TestQuestion(
                bot_id=bot_id,
                question=q_data["question"],
                display_order=q_data["display_order"]
            )
            session.add(new_question)
            added_count += 1
        
        await session.commit()
        print(f"   ✅ Bot ID {bot_id} ({bot.doctor_name}): {added_count} preguntas agregadas")
        return True


async def main():
    """Función principal - pobla automáticamente para todos los bots sin preguntas"""
    print("=" * 60)
    print("🔧 POBLAR PREGUNTAS DEL TEST DE ENDOMETRIOSIS (AUTOMÁTICO)")
    print("=" * 60)
    
    await init_engine()
    
    try:
        # Obtener preguntas desde cualquier bot que las tenga
        print("\n📋 Obteniendo preguntas desde un bot existente...")
        questions = await get_questions_from_bot(2)
        
        if not questions:
            print("❌ No se encontraron preguntas en Bot ID 2")
            return
        
        print(f"✅ Se encontraron {len(questions)} preguntas")
        
        # Listar todos los bots
        async with get_session() as session:
            stmt = select(Bot).order_by(Bot.id)
            result = await session.execute(stmt)
            bots = result.scalars().all()
        
        print(f"\n📋 Poblando preguntas para todos los bots...")
        print("-" * 60)
        
        populated_count = 0
        skipped_count = 0
        
        for bot in bots:
            # Verificar si ya tiene preguntas
            async with get_session() as session:
                stmt = select(TestQuestion).where(TestQuestion.bot_id == bot.id)
                result = await session.execute(stmt)
                existing_count = len(result.scalars().all())
            
            if existing_count == 0:
                success = await populate_test_questions(bot.id, questions, overwrite=False)
                if success:
                    populated_count += 1
            else:
                print(f"   ⏭️ Bot ID {bot.id} ({bot.doctor_name}) ya tiene {existing_count} preguntas, omitiendo")
                skipped_count += 1
        
        print("\n" + "=" * 60)
        print(f"✅ Proceso completado:")
        print(f"   • Bots poblados: {populated_count}")
        print(f"   • Bots omitidos (ya tenían preguntas): {skipped_count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_engine()


if __name__ == "__main__":
    asyncio.run(main())

