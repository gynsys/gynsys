"""
Script para debug: Simular el flujo del test y ver qué bot_id se está usando
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.session import get_session
from database.engine import init_engine, close_engine
from database import content_db
from common.context_manager import get_tenant_id
from utils.role_manager import RoleManager
from config import DB_PATH, SUPER_ADMIN_ID
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes
from unittest.mock import Mock
from sqlalchemy import select
from database.models.bot import Bot
from database.models.user import Doctor
from database.models.extra import TestQuestion


async def debug_test_flow(user_id: int = None):
    """Debug: Simular el flujo del test"""
    print("=" * 60)
    print("🔍 DEBUG: Flujo del Test de Endometriosis")
    print("=" * 60)
    
    await init_engine()
    role_manager = RoleManager(DB_PATH)
    
    if not user_id:
        # Pedir user_id
        user_id = int(input("Ingresa el Telegram ID del usuario que está probando el test: "))
    
    print(f"\n📋 Usuario ID: {user_id}")
    print("-" * 60)
    
    try:
        # 1. Verificar rol del usuario
        role = await role_manager.get_user_role(user_id)
        print(f"1. Rol del usuario: {role}")
        
        # 2. Simular get_tenant_id
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_chat = Mock(spec=Chat)
        mock_chat.id = user_id
        mock_message = Mock(spec=Message)
        mock_message.chat = mock_chat
        mock_update = Mock(spec=Update)
        mock_update.effective_user = mock_user
        mock_update.effective_chat = mock_chat
        mock_update.effective_message = mock_message
        
        mock_context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        mock_context.user_data = {}
        
        tenant_id = await get_tenant_id(mock_update, mock_context)
        print(f"2. Tenant ID (get_tenant_id): {tenant_id}")
        
        # 3. Simular _get_bot_id_for_test
        print("\n3. Simulando _get_bot_id_for_test:")
        
        # Si es doctor
        doctor = await role_manager.get_doctor_by_telegram_id(user_id)
        if doctor:
            print(f"   - Es doctor: ID={doctor[0]}, Telegram ID={doctor[2]}")
            async with get_session() as session:
                stmt = select(Bot.id).where(Bot.admin_user_id == doctor[2])
                result = await session.execute(stmt)
                bot_id = result.scalar_one_or_none()
                if bot_id:
                    print(f"   - Bot ID encontrado: {bot_id}")
                else:
                    print(f"   - ❌ No se encontró bot_id para este doctor")
        else:
            print(f"   - No es doctor")
        
        # Si es paciente
        doctor_id = mock_context.user_data.get("patient_doctor_id")
        if not doctor_id:
            assigned_doctor = await role_manager.get_assigned_doctor(user_id)
            if assigned_doctor:
                doctor_id = assigned_doctor[0]
                print(f"   - Doctor asignado encontrado: ID={doctor_id}")
        
        if doctor_id:
            async with get_session() as session:
                stmt_doctor = select(Doctor).where(Doctor.id == doctor_id)
                result_doctor = await session.execute(stmt_doctor)
                doctor_obj = result_doctor.scalar_one_or_none()
                if doctor_obj:
                    print(f"   - Doctor objeto: ID={doctor_obj.id}, Telegram ID={doctor_obj.telegram_id}")
                    stmt_bot = select(Bot.id).where(Bot.admin_user_id == doctor_obj.telegram_id)
                    result_bot = await session.execute(stmt_bot)
                    bot_id = result_bot.scalar_one_or_none()
                    if bot_id:
                        print(f"   - Bot ID encontrado: {bot_id}")
                    else:
                        print(f"   - ❌ No se encontró bot_id para este doctor")
        
        # 4. Obtener bot_id final (simulando la función completa)
        final_bot_id = tenant_id  # Fallback
        
        if doctor:
            doctor_telegram_id = doctor[2]
            async with get_session() as session:
                stmt = select(Bot.id).where(Bot.admin_user_id == doctor_telegram_id)
                result = await session.execute(stmt)
                bot_id_from_doctor = result.scalar_one_or_none()
                if bot_id_from_doctor:
                    final_bot_id = bot_id_from_doctor
        
        if doctor_id and not final_bot_id:
            async with get_session() as session:
                stmt_doctor = select(Doctor).where(Doctor.id == doctor_id)
                result_doctor = await session.execute(stmt_doctor)
                doctor_obj = result_doctor.scalar_one_or_none()
                if doctor_obj:
                    stmt_bot = select(Bot.id).where(Bot.admin_user_id == doctor_obj.telegram_id)
                    result_bot = await session.execute(stmt_bot)
                    bot_id_from_patient = result_bot.scalar_one_or_none()
                    if bot_id_from_patient:
                        final_bot_id = bot_id_from_patient
        
        print(f"\n4. Bot ID final que se usaría: {final_bot_id}")
        
        # 5. Verificar preguntas usando content_db
        if final_bot_id:
            print(f"\n5. Verificando preguntas para bot_id={final_bot_id}:")
            question_items = await content_db.get_all_items(final_bot_id, 'test_questions', 'question')
            questions = [item['title'] for item in question_items]
            print(f"   - Preguntas encontradas (content_db): {len(questions)}")
            
            if questions:
                print(f"   - Primera pregunta: {questions[0][:60]}...")
            else:
                print(f"   - ❌ No se encontraron preguntas usando content_db")
                
                # Verificar directamente en BD
                async with get_session() as session:
                    stmt = select(TestQuestion).where(TestQuestion.bot_id == final_bot_id)
                    result = await session.execute(stmt)
                    direct_questions = result.scalars().all()
                    print(f"   - Verificación directa en BD: {len(direct_questions)} preguntas")
                    if direct_questions:
                        print(f"   - ⚠️ Hay preguntas en BD pero content_db no las encuentra")
                        print(f"   - Primera pregunta en BD: {direct_questions[0].question[:60]}...")
        
        print("\n" + "=" * 60)
        print("✅ Debug completado")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_engine()


if __name__ == "__main__":
    import sys
    user_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    asyncio.run(debug_test_flow(user_id))

