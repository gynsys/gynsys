"""
Script para verificar qué bots están asociados a un doctor específico
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


async def check_doctor_bots(telegram_id: int = 5057356565):
    """Verifica qué bots están asociados a un doctor"""
    print("=" * 60)
    print(f"🔍 VERIFICACIÓN: Bots para Doctor (Telegram ID: {telegram_id})")
    print("=" * 60)
    
    await init_engine()
    
    try:
        async with get_session() as session:
            # Buscar doctor
            stmt_doctor = select(Doctor).where(Doctor.telegram_id == telegram_id)
            result_doctor = await session.execute(stmt_doctor)
            doctor = result_doctor.scalar_one_or_none()
            
            if not doctor:
                print(f"❌ No se encontró doctor con telegram_id={telegram_id}")
                return
            
            print(f"\n📋 Doctor encontrado:")
            print(f"   ID: {doctor.id}")
            print(f"   Nombre: {doctor.name}")
            print(f"   Telegram ID: {doctor.telegram_id}")
            print(f"   Activo: {doctor.is_active}")
            
            # Buscar todos los bots asociados a este doctor
            stmt_bots = select(Bot).where(Bot.admin_user_id == telegram_id)
            result_bots = await session.execute(stmt_bots)
            bots = result_bots.scalars().all()
            
            print(f"\n📋 Bots asociados a este doctor:")
            print("-" * 60)
            if not bots:
                print("   ❌ No se encontraron bots")
            else:
                for bot in bots:
                    # Contar preguntas
                    stmt_questions = select(TestQuestion).where(TestQuestion.bot_id == bot.id)
                    result_questions = await session.execute(stmt_questions)
                    question_count = len(result_questions.scalars().all())
                    
                    print(f"   Bot ID: {bot.id}")
                    print(f"   Nombre: {bot.doctor_name}")
                    print(f"   Admin User ID: {bot.admin_user_id}")
                    print(f"   Preguntas del test: {question_count}")
                    print()
            
            print("=" * 60)
            print("✅ Verificación completada")
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_engine()


if __name__ == "__main__":
    import sys
    telegram_id = int(sys.argv[1]) if len(sys.argv) > 1 else 5057356565
    asyncio.run(check_doctor_bots(telegram_id))

