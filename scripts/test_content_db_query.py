"""
Script para probar la consulta de content_db.get_all_items para test_questions
"""
import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.session import get_session
from database.engine import init_engine, close_engine
from database import content_db
from sqlalchemy import select
from database.models.extra import TestQuestion


async def test_content_db_query():
    """Prueba la consulta de content_db para test_questions"""
    print("=" * 60)
    print("🔍 PRUEBA: content_db.get_all_items para test_questions")
    print("=" * 60)
    
    await init_engine()
    
    try:
        # Probar con diferentes bot_ids
        test_bot_ids = [1, 2, 5]
        
        for bot_id in test_bot_ids:
            print(f"\n📋 Probando bot_id={bot_id}:")
            print("-" * 60)
            
            # 1. Usar content_db.get_all_items
            print("1. Usando content_db.get_all_items:")
            try:
                question_items = await content_db.get_all_items(bot_id, 'test_questions', 'question')
                questions = [item['title'] for item in question_items]
                print(f"   Resultado: {len(questions)} preguntas encontradas")
                if questions:
                    print(f"   Primera pregunta: {questions[0][:60]}...")
                else:
                    print(f"   ❌ No se encontraron preguntas")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            # 2. Consulta directa con SQLAlchemy
            print("\n2. Consulta directa con SQLAlchemy:")
            try:
                async with get_session() as session:
                    stmt = select(TestQuestion).where(TestQuestion.bot_id == bot_id).order_by(TestQuestion.display_order)
                    result = await session.execute(stmt)
                    direct_questions = result.scalars().all()
                    print(f"   Resultado: {len(direct_questions)} preguntas encontradas")
                    if direct_questions:
                        print(f"   Primera pregunta: {direct_questions[0].question[:60]}...")
                    else:
                        print(f"   ❌ No se encontraron preguntas")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            # 3. Consulta SQL directa (simulando lo que hace get_all_items)
            print("\n3. Consulta SQL directa (simulando get_all_items):")
            try:
                from sqlalchemy import text
                async with get_session() as session:
                    query = text("""
                        SELECT id, question as title 
                        FROM test_questions 
                        WHERE bot_id = :bot_id 
                        ORDER BY display_order, question
                    """)
                    result = await session.execute(query, {'bot_id': bot_id})
                    rows = result.all()
                    print(f"   Resultado: {len(rows)} preguntas encontradas")
                    if rows:
                        print(f"   Primera pregunta: {rows[0][1][:60]}...")
                    else:
                        print(f"   ❌ No se encontraron preguntas")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("✅ Prueba completada")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_engine()


if __name__ == "__main__":
    asyncio.run(test_content_db_query())

