"""
Script para poblar preguntas del test para TODOS los bots en producción.
Ejecutar este script en el servidor de producción.
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


# Preguntas por defecto del test de endometriosis
DEFAULT_TEST_QUESTIONS = [
    {
        "question": "¿Experimentas dolor pélvico intenso durante la menstruación que interfiere con tus actividades diarias?",
        "display_order": 0
    },
    {
        "question": "¿Tienes dolor durante o después de las relaciones sexuales?",
        "display_order": 1
    },
    {
        "question": "¿Sufres de dolor al orinar o al defecar, especialmente durante la menstruación?",
        "display_order": 2
    },
    {
        "question": "¿Has sido diagnosticada previamente con infertilidad o tienes dificultades para concebir?",
        "display_order": 3
    },
    {
        "question": "¿Experimentas fatiga crónica o falta de energía sin una causa aparente?",
        "display_order": 4
    },
    {
        "question": "¿Tienes problemas digestivos como hinchazón, estreñimiento o diarrea, especialmente durante la menstruación?",
        "display_order": 5
    },
    {
        "question": "¿Experimentas sangrado menstrual abundante o irregular?",
        "display_order": 6
    },
    {
        "question": "¿Sientes dolor en la parte baja de la espalda o en las piernas durante la menstruación?",
        "display_order": 7
    },
    {
        "question": "¿Has tenido quistes ováricos o masas pélvicas detectadas en exámenes médicos?",
        "display_order": 8
    },
    {
        "question": "¿Tienes antecedentes familiares de endometriosis (madre, tía, hermana)?",
        "display_order": 9
    }
]


async def get_questions_from_bot(source_bot_id: int):
    """Obtiene las preguntas de un bot existente"""
    async with get_session() as session:
        stmt = select(TestQuestion).where(TestQuestion.bot_id == source_bot_id).order_by(TestQuestion.display_order)
        result = await session.execute(stmt)
        questions = result.scalars().all()
        if questions:
            return [
                {
                    "question": q.question,
                    "display_order": q.display_order
                }
                for q in questions
            ]
    return None


async def populate_bot_questions(bot_id: int, questions: list, overwrite: bool = False):
    """Pobla las preguntas del test para un bot específico"""
    async with get_session() as session:
        # Verificar si el bot existe
        stmt_bot = select(Bot).where(Bot.id == bot_id)
        result_bot = await session.execute(stmt_bot)
        bot = result_bot.scalar_one_or_none()
        
        if not bot:
            print(f"   ❌ Bot ID {bot_id} no existe")
            return False
        
        # Verificar si ya existen preguntas
        stmt_existing = select(TestQuestion).where(TestQuestion.bot_id == bot_id)
        result_existing = await session.execute(stmt_existing)
        existing_questions = result_existing.scalars().all()
        
        if existing_questions:
            if overwrite:
                print(f"   ⚠️ Eliminando {len(existing_questions)} preguntas existentes...")
                for q in existing_questions:
                    await session.delete(q)
                await session.commit()
            else:
                print(f"   ⏭️ Ya tiene {len(existing_questions)} preguntas, omitiendo")
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
        print(f"   ✅ {added_count} preguntas agregadas para Bot ID {bot_id} ({bot.doctor_name})")
        return True


async def main():
    """Función principal"""
    print("=" * 60)
    print("🔧 POBLAR PREGUNTAS DEL TEST PARA TODOS LOS BOTS")
    print("=" * 60)
    
    await init_engine()
    
    try:
        # Obtener todas las preguntas desde cualquier bot que las tenga, o usar las por defecto
        questions = None
        async with get_session() as session:
            stmt = select(Bot).order_by(Bot.id)
            result = await session.execute(stmt)
            all_bots = result.scalars().all()
            
            # Buscar un bot que tenga preguntas
            for bot in all_bots:
                questions = await get_questions_from_bot(bot.id)
                if questions:
                    print(f"📋 Preguntas obtenidas desde Bot ID {bot.id}")
                    break
        
        if not questions:
            questions = DEFAULT_TEST_QUESTIONS
            print(f"📋 Usando preguntas por defecto")
        
        print(f"✅ Total de preguntas: {len(questions)}\n")
        
        # Poblar para todos los bots
        print("📋 Poblando preguntas para todos los bots...")
        print("-" * 60)
        
        populated_count = 0
        skipped_count = 0
        
        async with get_session() as session:
            stmt = select(Bot).order_by(Bot.id)
            result = await session.execute(stmt)
            all_bots = result.scalars().all()
        
        for bot in all_bots:
            success = await populate_bot_questions(bot.id, questions, overwrite=False)
            if success:
                populated_count += 1
            else:
                skipped_count += 1
        
        print("\n" + "=" * 60)
        print(f"✅ Proceso completado:")
        print(f"   • Bots poblados: {populated_count}")
        print(f"   • Bots omitidos: {skipped_count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_engine()


if __name__ == "__main__":
    asyncio.run(main())

