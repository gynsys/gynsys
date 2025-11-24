"""
Script para debug: Verificar qué bot_id se obtiene para un usuario específico
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.session import get_session
from database.engine import init_engine, close_engine
from database import user_db
from common.context_manager import get_tenant_id
from database import content_db
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes
from unittest.mock import Mock


async def debug_test_bot_id():
    """Debug: Verificar bot_id para usuarios"""
    print("=" * 60)
    print("🔍 DEBUG: Bot ID para Test de Endometriosis")
    print("=" * 60)
    
    await init_engine()
    
    try:
        async with get_session() as session:
            # Probar con diferentes usuarios
            test_user_ids = [5057356565, 1035216286]  # MARI y SuperAdmin
            
            for user_id in test_user_ids:
                print(f"\n📋 Usuario ID: {user_id}")
                print("-" * 60)
                
                # Obtener tenant_id usando user_db
                tenant_id = await user_db.get_user_tenant(user_id)
                print(f"  Tenant ID (user_db.get_user_tenant): {tenant_id}")
                
                # Simular un update para get_tenant_id
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
                
                # Obtener tenant_id usando get_tenant_id
                tenant_id_from_context = await get_tenant_id(mock_update, mock_context)
                print(f"  Tenant ID (get_tenant_id): {tenant_id_from_context}")
                
                # Obtener preguntas usando content_db
                if tenant_id_from_context:
                    question_items = await content_db.get_all_items(tenant_id_from_context, 'test_questions', 'question')
                    questions = [item['title'] for item in question_items]
                    print(f"  Preguntas encontradas: {len(questions)}")
                    if questions:
                        print(f"    Primera pregunta: {questions[0][:60]}...")
                    else:
                        print(f"    ❌ No se encontraron preguntas para bot_id={tenant_id_from_context}")
                        
                        # Verificar directamente en la BD
                        from sqlalchemy import select
                        from database.models.extra import TestQuestion
                        stmt = select(TestQuestion).where(TestQuestion.bot_id == tenant_id_from_context)
                        result = await session.execute(stmt)
                        direct_questions = result.scalars().all()
                        print(f"    Verificación directa en BD: {len(direct_questions)} preguntas")
                        if direct_questions:
                            print(f"      ⚠️ Hay preguntas en BD pero content_db no las encuentra")
                            print(f"      Primera pregunta en BD: {direct_questions[0].question[:60]}...")
            
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
    asyncio.run(debug_test_bot_id())

