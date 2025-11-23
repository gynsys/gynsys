"""
Script para verificar todos los doctores y bots en la base de datos
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.session import get_session
from database.engine import init_engine, close_engine
from sqlalchemy import select
from database.models.user import Doctor
from database.models.bot import Bot


async def check_all_doctors_and_bots():
    """Verifica todos los doctores y bots en la BD"""
    print("=" * 60)
    print("🔍 VERIFICACIÓN: Doctores y Bots en la Base de Datos")
    print("=" * 60)
    
    await init_engine()
    
    try:
        async with get_session() as session:
            # Todos los doctores
            print("\n📋 TABLA: doctors")
            print("-" * 60)
            stmt_doctors = select(Doctor)
            result_doctors = await session.execute(stmt_doctors)
            all_doctors = result_doctors.scalars().all()
            print(f"Total doctores: {len(all_doctors)}")
            for doctor in all_doctors:
                print(f"  • ID: {doctor.id}, Nombre: {doctor.name}, Telegram ID: {doctor.telegram_id}, Activo: {doctor.is_active}")
            
            # Todos los bots
            print("\n📋 TABLA: bots")
            print("-" * 60)
            stmt_bots = select(Bot)
            result_bots = await session.execute(stmt_bots)
            all_bots = result_bots.scalars().all()
            print(f"Total bots: {len(all_bots)}")
            for bot in all_bots:
                print(f"  • Bot ID: {bot.id}, Nombre: {bot.doctor_name}, Admin User ID: {bot.admin_user_id}, Activo: {bot.is_active}")
            
            # Verificar si hay bots con admin_user_id que no estén en doctors
            print("\n📋 VERIFICACIÓN: Bots sin doctor correspondiente")
            print("-" * 60)
            doctor_ids = {d.id for d in all_doctors}
            doctor_telegram_ids = {d.telegram_id for d in all_doctors}
            
            bots_without_doctor = []
            for bot in all_bots:
                # Verificar por telegram_id (admin_user_id)
                if bot.admin_user_id not in doctor_telegram_ids:
                    bots_without_doctor.append(bot)
                    print(f"  ⚠️ Bot ID {bot.id} tiene admin_user_id {bot.admin_user_id} que NO está en doctors")
            
            if not bots_without_doctor:
                print("  ✅ Todos los bots tienen un doctor correspondiente")
            
            # Verificar si hay doctores sin bot
            print("\n📋 VERIFICACIÓN: Doctores sin bot correspondiente")
            print("-" * 60)
            bot_admin_ids = {b.admin_user_id for b in all_bots}
            
            doctors_without_bot = []
            for doctor in all_doctors:
                if doctor.telegram_id not in bot_admin_ids:
                    doctors_without_bot.append(doctor)
                    print(f"  ⚠️ Doctor ID {doctor.id} ({doctor.name}) tiene telegram_id {doctor.telegram_id} que NO tiene bot")
            
            if not doctors_without_bot:
                print("  ✅ Todos los doctores tienen un bot correspondiente")
            
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
    asyncio.run(check_all_doctors_and_bots())

