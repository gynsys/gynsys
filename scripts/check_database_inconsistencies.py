"""
Script para verificar inconsistencias en la base de datos después de la migración a SQLAlchemy.
Especialmente para detectar múltiples bots para el mismo doctor o datos duplicados.
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.session import get_session
from database.engine import init_engine, close_engine
from sqlalchemy import select, func
from database.models.bot import Bot
from database.models.user import Doctor
from database.models.extra import TestQuestion, ExtraModule


async def check_inconsistencies():
    """Verifica inconsistencias en la base de datos"""
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE INCONSISTENCIAS EN LA BASE DE DATOS")
    print("=" * 60)
    
    await init_engine()
    
    try:
        async with get_session() as session:
            # 1. Verificar múltiples bots para el mismo doctor
            print("\n1. Verificando múltiples bots para el mismo doctor:")
            print("-" * 60)
            stmt = select(Bot.admin_user_id, func.count(Bot.id).label('count')).group_by(Bot.admin_user_id).having(func.count(Bot.id) > 1)
            result = await session.execute(stmt)
            duplicates = result.all()
            
            if duplicates:
                print(f"   ⚠️ Se encontraron {len(duplicates)} doctores con múltiples bots:")
                for admin_user_id, count in duplicates:
                    stmt_bots = select(Bot).where(Bot.admin_user_id == admin_user_id)
                    result_bots = await session.execute(stmt_bots)
                    bots = result_bots.scalars().all()
                    print(f"\n   Doctor Telegram ID: {admin_user_id} ({count} bots)")
                    for bot in bots:
                        # Contar preguntas
                        stmt_questions = select(TestQuestion).where(TestQuestion.bot_id == bot.id)
                        result_questions = await session.execute(stmt_questions)
                        question_count = len(result_questions.scalars().all())
                        print(f"      - Bot ID: {bot.id}, Nombre: {bot.doctor_name}, Preguntas: {question_count}")
            else:
                print("   ✅ No se encontraron doctores con múltiples bots")
            
            # 2. Verificar bots sin doctor asociado
            print("\n2. Verificando bots sin doctor asociado:")
            print("-" * 60)
            stmt_all_bots = select(Bot)
            result_all_bots = await session.execute(stmt_all_bots)
            all_bots = result_all_bots.scalars().all()
            
            orphaned_bots = []
            for bot in all_bots:
                stmt_doctor = select(Doctor).where(Doctor.telegram_id == bot.admin_user_id)
                result_doctor = await session.execute(stmt_doctor)
                doctor = result_doctor.scalar_one_or_none()
                if not doctor:
                    orphaned_bots.append(bot)
            
            if orphaned_bots:
                print(f"   ⚠️ Se encontraron {len(orphaned_bots)} bots sin doctor asociado:")
                for bot in orphaned_bots:
                    print(f"      - Bot ID: {bot.id}, Nombre: {bot.doctor_name}, Admin User ID: {bot.admin_user_id}")
            else:
                print("   ✅ Todos los bots tienen un doctor asociado")
            
            # 3. Verificar doctores sin bot
            print("\n3. Verificando doctores sin bot:")
            print("-" * 60)
            stmt_all_doctors = select(Doctor)
            result_all_doctors = await session.execute(stmt_all_doctors)
            all_doctors = result_all_doctors.scalars().all()
            
            doctors_without_bot = []
            for doctor in all_doctors:
                stmt_bot = select(Bot).where(Bot.admin_user_id == doctor.telegram_id)
                result_bot = await session.execute(stmt_bot)
                bot = result_bot.scalar_one_or_none()
                if not bot:
                    doctors_without_bot.append(doctor)
            
            if doctors_without_bot:
                print(f"   ⚠️ Se encontraron {len(doctors_without_bot)} doctores sin bot:")
                for doctor in doctors_without_bot:
                    print(f"      - Doctor ID: {doctor.id}, Nombre: {doctor.name}, Telegram ID: {doctor.telegram_id}")
            else:
                print("   ✅ Todos los doctores tienen un bot asociado")
            
            # 4. Verificar preguntas del test en bots huérfanos o duplicados
            print("\n4. Verificando distribución de preguntas del test:")
            print("-" * 60)
            stmt_questions = select(TestQuestion.bot_id, func.count(TestQuestion.id).label('count')).group_by(TestQuestion.bot_id)
            result_questions = await session.execute(stmt_questions)
            question_distribution = result_questions.all()
            
            for bot_id, count in question_distribution:
                stmt_bot = select(Bot).where(Bot.id == bot_id)
                result_bot = await session.execute(stmt_bot)
                bot = result_bot.scalar_one_or_none()
                if bot:
                    print(f"   Bot ID {bot_id} ({bot.doctor_name}): {count} preguntas")
                else:
                    print(f"   ⚠️ Bot ID {bot_id} (NO EXISTE): {count} preguntas")
            
            # 5. Resumen de problemas
            print("\n" + "=" * 60)
            print("📋 RESUMEN DE PROBLEMAS:")
            print("=" * 60)
            
            problems = []
            if duplicates:
                problems.append(f"⚠️ {len(duplicates)} doctores con múltiples bots")
            if orphaned_bots:
                problems.append(f"⚠️ {len(orphaned_bots)} bots sin doctor asociado")
            if doctors_without_bot:
                problems.append(f"⚠️ {len(doctors_without_bot)} doctores sin bot")
            
            if problems:
                for problem in problems:
                    print(f"   {problem}")
            else:
                print("   ✅ No se encontraron problemas")
            
            print("=" * 60)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_engine()


if __name__ == "__main__":
    asyncio.run(check_inconsistencies())

