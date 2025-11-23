"""
Script para poblar preguntas del test para un bot_id específico
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


async def populate_bot_questions(target_bot_id: int, source_bot_id: int = 2):
    """
    Pobla las preguntas del test para un bot_id específico.
    
    Args:
        target_bot_id: ID del bot al que se le agregarán las preguntas
        source_bot_id: ID del bot del cual copiar las preguntas (default: 2)
    """
    await init_engine()
    
    try:
        async with get_session() as session:
            # Verificar si el bot destino existe
            stmt_bot = select(Bot).where(Bot.id == target_bot_id)
            result_bot = await session.execute(stmt_bot)
            bot = result_bot.scalar_one_or_none()
            
            if not bot:
                print(f"❌ Error: No se encontró el bot con ID {target_bot_id}")
                return False
            
            print(f"📋 Bot destino: ID={target_bot_id}, Nombre={bot.doctor_name}")
            
            # Obtener preguntas desde bot origen
            print(f"📋 Obteniendo preguntas desde Bot ID {source_bot_id}...")
            questions = await get_questions_from_bot(source_bot_id)
            
            if not questions:
                print(f"❌ No se encontraron preguntas en Bot ID {source_bot_id}")
                return False
            
            print(f"✅ Se encontraron {len(questions)} preguntas")
            
            # Verificar si ya existen preguntas
            stmt_existing = select(TestQuestion).where(TestQuestion.bot_id == target_bot_id)
            result_existing = await session.execute(stmt_existing)
            existing_questions = result_existing.scalars().all()
            
            if existing_questions:
                print(f"   ⚠️ Ya existen {len(existing_questions)} preguntas para este bot")
                print(f"   Eliminando preguntas existentes...")
                for q in existing_questions:
                    await session.delete(q)
                await session.commit()
            
            # Agregar nuevas preguntas
            added_count = 0
            for q_data in questions:
                new_question = TestQuestion(
                    bot_id=target_bot_id,
                    question=q_data["question"],
                    display_order=q_data["display_order"]
                )
                session.add(new_question)
                added_count += 1
            
            await session.commit()
            print(f"   ✅ {added_count} preguntas agregadas exitosamente")
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await close_engine()


async def main():
    """Función principal"""
    print("=" * 60)
    print("🔧 POBLAR PREGUNTAS DEL TEST PARA BOT ESPECÍFICO")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nUso: python scripts/populate_specific_bot.py <bot_id> [source_bot_id]")
        print("Ejemplo: python scripts/populate_specific_bot.py 4 2")
        return
    
    target_bot_id = int(sys.argv[1])
    source_bot_id = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    
    success = await populate_bot_questions(target_bot_id, source_bot_id)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Proceso completado exitosamente")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Proceso falló")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

