"""
Script para verificar las preguntas del test de endometriosis en la base de datos
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


async def check_test_questions():
    """Verifica las preguntas del test en la BD"""
    print("=" * 60)
    print("🔍 VERIFICACIÓN: Preguntas del Test de Endometriosis")
    print("=" * 60)
    
    await init_engine()
    
    try:
        async with get_session() as session:
            # Obtener todos los bots
            print("\n📋 Bots en la base de datos:")
            print("-" * 60)
            stmt_bots = select(Bot)
            result_bots = await session.execute(stmt_bots)
            all_bots = result_bots.scalars().all()
            print(f"Total bots: {len(all_bots)}")
            
            for bot in all_bots:
                print(f"\n  Bot ID: {bot.id}, Nombre: {bot.doctor_name}, Admin User ID: {bot.admin_user_id}")
                
                # Obtener preguntas para este bot
                stmt_questions = select(TestQuestion).where(TestQuestion.bot_id == bot.id).order_by(TestQuestion.display_order)
                result_questions = await session.execute(stmt_questions)
                questions = result_questions.scalars().all()
                
                print(f"    Preguntas para este bot: {len(questions)}")
                for i, question in enumerate(questions, 1):
                    print(f"      {i}. ID: {question.id}, Orden: {question.display_order}, Pregunta: {question.question[:50]}...")
            
            # Obtener todas las preguntas sin filtrar por bot
            print("\n📋 Todas las preguntas del test (sin filtrar):")
            print("-" * 60)
            stmt_all_questions = select(TestQuestion).order_by(TestQuestion.bot_id, TestQuestion.display_order)
            result_all = await session.execute(stmt_all_questions)
            all_questions = result_all.scalars().all()
            print(f"Total preguntas en BD: {len(all_questions)}")
            
            if all_questions:
                for question in all_questions:
                    print(f"  • Bot ID: {question.bot_id}, Orden: {question.display_order}, Pregunta: {question.question[:60]}...")
            else:
                print("  ❌ No hay preguntas en la base de datos")
            
            # Verificar relación bot-doctor
            print("\n📋 Verificación: Relación Bot-Doctor:")
            print("-" * 60)
            for bot in all_bots:
                # Buscar doctor por admin_user_id
                stmt_doctor = select(Doctor).where(Doctor.telegram_id == bot.admin_user_id)
                result_doctor = await session.execute(stmt_doctor)
                doctor = result_doctor.scalar_one_or_none()
                
                if doctor:
                    print(f"  Bot ID {bot.id} → Doctor ID {doctor.id} ({doctor.name})")
                else:
                    print(f"  ⚠️ Bot ID {bot.id} → No se encontró doctor con telegram_id {bot.admin_user_id}")
            
            print("\n" + "=" * 60)
            print("✅ Verificación completada")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_engine()


if __name__ == "__main__":
    asyncio.run(check_test_questions())

