"""
Script para poblar las preguntas del test de endometriosis en la base de datos.
Copia las preguntas de un bot existente a otros bots, o crea las preguntas por defecto.
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
from database.models.user import Doctor


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
        return [
            {
                "question": q.question,
                "display_order": q.display_order
            }
            for q in questions
        ]


async def populate_test_questions(bot_id: int, questions: list = None, source_bot_id: int = None):
    """
    Pobla las preguntas del test para un bot específico.
    
    Args:
        bot_id: ID del bot al que se le agregarán las preguntas
        questions: Lista de preguntas a agregar (opcional)
        source_bot_id: ID del bot del cual copiar las preguntas (opcional)
    """
    async with get_session() as session:
        # Verificar si el bot existe
        stmt_bot = select(Bot).where(Bot.id == bot_id)
        result_bot = await session.execute(stmt_bot)
        bot = result_bot.scalar_one_or_none()
        
        if not bot:
            print(f"❌ Error: No se encontró el bot con ID {bot_id}")
            return False
        
        print(f"📋 Poblando preguntas para Bot ID: {bot_id} ({bot.doctor_name})")
        
        # Obtener preguntas
        if source_bot_id:
            questions = await get_questions_from_bot(source_bot_id)
            print(f"   Copiando preguntas desde Bot ID: {source_bot_id}")
        elif not questions:
            questions = DEFAULT_TEST_QUESTIONS
            print(f"   Usando preguntas por defecto")
        
        # Verificar si ya existen preguntas
        stmt_existing = select(TestQuestion).where(TestQuestion.bot_id == bot_id)
        result_existing = await session.execute(stmt_existing)
        existing_questions = result_existing.scalars().all()
        
        if existing_questions:
            print(f"   ⚠️ Ya existen {len(existing_questions)} preguntas para este bot")
            response = input(f"   ¿Deseas eliminar las preguntas existentes y agregar las nuevas? (s/n): ")
            if response.lower() == 's':
                for q in existing_questions:
                    await session.delete(q)
                await session.commit()
                print(f"   ✅ Preguntas existentes eliminadas")
            else:
                print(f"   ⏭️ Manteniendo preguntas existentes")
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
        print(f"   ✅ {added_count} preguntas agregadas exitosamente")
        return True


async def list_all_bots():
    """Lista todos los bots en la base de datos"""
    async with get_session() as session:
        stmt = select(Bot).order_by(Bot.id)
        result = await session.execute(stmt)
        bots = result.scalars().all()
        return bots


async def main():
    """Función principal"""
    print("=" * 60)
    print("🔧 POBLAR PREGUNTAS DEL TEST DE ENDOMETRIOSIS")
    print("=" * 60)
    
    await init_engine()
    
    try:
        # Listar todos los bots
        bots = await list_all_bots()
        print(f"\n📋 Bots disponibles:")
        print("-" * 60)
        for bot in bots:
            # Contar preguntas existentes
            async with get_session() as session:
                stmt = select(TestQuestion).where(TestQuestion.bot_id == bot.id)
                result = await session.execute(stmt)
                question_count = len(result.scalars().all())
            print(f"  {bot.id}. {bot.doctor_name} (Admin: {bot.admin_user_id}) - {question_count} preguntas")
        
        print("\n" + "-" * 60)
        print("Opciones:")
        print("1. Poblar preguntas para un bot específico")
        print("2. Copiar preguntas de un bot a otro")
        print("3. Poblar preguntas para todos los bots sin preguntas")
        print("-" * 60)
        
        option = input("\nSelecciona una opción (1/2/3): ").strip()
        
        if option == "1":
            bot_id = int(input("Ingresa el ID del bot: "))
            populate_all = input("¿Usar preguntas por defecto? (s/n): ").lower() == 's'
            if populate_all:
                await populate_test_questions(bot_id)
            else:
                source_bot_id = int(input("Ingresa el ID del bot del cual copiar las preguntas: "))
                await populate_test_questions(bot_id, source_bot_id=source_bot_id)
        
        elif option == "2":
            source_bot_id = int(input("Ingresa el ID del bot origen: "))
            target_bot_id = int(input("Ingresa el ID del bot destino: "))
            await populate_test_questions(target_bot_id, source_bot_id=source_bot_id)
        
        elif option == "3":
            bots = await list_all_bots()
            for bot in bots:
                async with get_session() as session:
                    stmt = select(TestQuestion).where(TestQuestion.bot_id == bot.id)
                    result = await session.execute(stmt)
                    question_count = len(result.scalars().all())
                if question_count == 0:
                    print(f"\n📋 Poblando preguntas para Bot ID: {bot.id} ({bot.doctor_name})")
                    await populate_test_questions(bot.id)
        
        else:
            print("❌ Opción inválida")
        
        print("\n" + "=" * 60)
        print("✅ Proceso completado")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_engine()


if __name__ == "__main__":
    asyncio.run(main())

