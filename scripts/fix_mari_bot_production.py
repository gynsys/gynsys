"""
Script para corregir el problema del bot de MARI en producción.
Este script debe ejecutarse en el servidor de producción.
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.session import get_session
from database.engine import init_engine, close_engine
from sqlalchemy import select
from database.models.bot import Bot
from database.models.user import Doctor
from database.models.extra import TestQuestion

MARI_TELEGRAM_ID = 5057356565


async def fix_mari_bot():
    """Corrige el problema del bot de MARI"""
    print("=" * 60)
    print("🔧 CORRECCIÓN: Bot de maariel2 en Producción")
    print("=" * 60)
    
    await init_engine()
    
    try:
        async with get_session() as session:
            # 1. Buscar todos los bots de maariel2
            print(f"\n1. Buscando bots para maariel2 (Telegram ID: {MARI_TELEGRAM_ID}):")
            print("-" * 60)
            stmt_bots = select(Bot).where(Bot.admin_user_id == MARI_TELEGRAM_ID)
            result_bots = await session.execute(stmt_bots)
            mari_bots = result_bots.scalars().all()
            
            if not mari_bots:
                print("   ❌ No se encontraron bots para maariel2")
                return
            
            print(f"   Se encontraron {len(mari_bots)} bot(s):")
            for bot in mari_bots:
                # Contar preguntas
                stmt_questions = select(TestQuestion).where(TestQuestion.bot_id == bot.id)
                result_questions = await session.execute(stmt_questions)
                question_count = len(result_questions.scalars().all())
                print(f"      - Bot ID: {bot.id}, Nombre: {bot.doctor_name}, Preguntas: {question_count}")
            
            # 2. Identificar el bot principal (el que tiene más datos o el más reciente)
            if len(mari_bots) > 1:
                print(f"\n   ⚠️ Se encontraron múltiples bots. Necesitamos consolidar.")
                # Usar el bot con más preguntas, o el más reciente
                main_bot = None
                max_questions = 0
                for bot in mari_bots:
                    stmt_questions = select(TestQuestion).where(TestQuestion.bot_id == bot.id)
                    result_questions = await session.execute(stmt_questions)
                    question_count = len(result_questions.scalars().all())
                    if question_count > max_questions:
                        max_questions = question_count
                        main_bot = bot
                
                if not main_bot:
                    main_bot = mari_bots[0]  # Usar el primero si no hay preguntas
                
                print(f"   Bot principal seleccionado: Bot ID {main_bot.id}")
            else:
                main_bot = mari_bots[0]
                print(f"\n   Bot único: Bot ID {main_bot.id}")
            
            # 3. Obtener preguntas desde el bot principal o desde otro bot que las tenga
            print(f"\n2. Obteniendo preguntas del test:")
            print("-" * 60)
            
            # Buscar un bot que tenga preguntas
            source_bot = None
            for bot in mari_bots:
                stmt_questions = select(TestQuestion).where(TestQuestion.bot_id == bot.id)
                result_questions = await session.execute(stmt_questions)
                questions = result_questions.scalars().all()
                if questions:
                    source_bot = bot
                    break
            
            if not source_bot:
                # Buscar en otros bots
                stmt_all_bots = select(Bot)
                result_all_bots = await session.execute(stmt_all_bots)
                all_bots = result_all_bots.scalars().all()
                for bot in all_bots:
                    stmt_questions = select(TestQuestion).where(TestQuestion.bot_id == bot.id)
                    result_questions = await session.execute(stmt_questions)
                    questions = result_questions.scalars().all()
                    if questions:
                        source_bot = bot
                        break
            
            if source_bot:
                stmt_questions = select(TestQuestion).where(TestQuestion.bot_id == source_bot.id).order_by(TestQuestion.display_order)
                result_questions = await session.execute(stmt_questions)
                source_questions = result_questions.scalars().all()
                print(f"   Preguntas obtenidas desde Bot ID {source_bot.id}: {len(source_questions)} preguntas")
            else:
                print("   ❌ No se encontraron preguntas en ningún bot")
                print("   Usando preguntas por defecto...")
                source_questions = None
            
            # 4. Poblar preguntas para todos los bots de maariel2 que no las tengan
            print(f"\n3. Poblando preguntas para todos los bots de maariel2:")
            print("-" * 60)
            
            for bot in mari_bots:
                # Verificar si ya tiene preguntas
                stmt_existing = select(TestQuestion).where(TestQuestion.bot_id == bot.id)
                result_existing = await session.execute(stmt_existing)
                existing_questions = result_existing.scalars().all()
                
                if existing_questions:
                    print(f"   Bot ID {bot.id}: Ya tiene {len(existing_questions)} preguntas, omitiendo")
                else:
                    print(f"   Bot ID {bot.id}: No tiene preguntas, agregando...")
                    
                    if source_questions:
                        # Copiar desde otro bot
                        for q in source_questions:
                            new_question = TestQuestion(
                                bot_id=bot.id,
                                question=q.question,
                                display_order=q.display_order
                            )
                            session.add(new_question)
                    else:
                        # Usar preguntas por defecto
                        default_questions = [
                            "¿Experimentas dolor pélvico intenso durante la menstruación que interfiere con tus actividades diarias?",
                            "¿Tienes dolor durante o después de las relaciones sexuales?",
                            "¿Sufres de dolor al orinar o al defecar, especialmente durante la menstruación?",
                            "¿Has sido diagnosticada previamente con infertilidad o tienes dificultades para concebir?",
                            "¿Experimentas fatiga crónica o falta de energía sin una causa aparente?",
                            "¿Tienes problemas digestivos como hinchazón, estreñimiento o diarrea, especialmente durante la menstruación?",
                            "¿Experimentas sangrado menstrual abundante o irregular?",
                            "¿Sientes dolor en la parte baja de la espalda o en las piernas durante la menstruación?",
                            "¿Has tenido quistes ováricos o masas pélvicas detectadas en exámenes médicos?",
                            "¿Tienes antecedentes familiares de endometriosis (madre, tía, hermana)?"
                        ]
                        for i, question_text in enumerate(default_questions):
                            new_question = TestQuestion(
                                bot_id=bot.id,
                                question=question_text,
                                display_order=i
                            )
                            session.add(new_question)
                    
                    await session.commit()
                    print(f"      ✅ Preguntas agregadas exitosamente")
            
            print("\n" + "=" * 60)
            print("✅ Proceso completado")
            print("=" * 60)
            print("\n📋 Instrucciones:")
            print("   1. Verifica que todos los bots de maariel2 ahora tienen preguntas")
            print("   2. Prueba el test desde el bot para confirmar que funciona")
            print("   3. Si hay múltiples bots, considera consolidarlos en uno solo")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_engine()


if __name__ == "__main__":
    asyncio.run(fix_mari_bot())

