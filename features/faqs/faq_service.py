"""
Servicio CRUD de FAQs – multi-tenant.
Mismo nombre de archivo para no romper imports.
"""
from typing import Optional, List, Dict
from sqlalchemy import select, func
from database.session import get_session
from database.models.content import FAQ

async def add_faq(bot_id: int, question: str, answer: str) -> Optional[int]:
    async with get_session() as session:
        max_order = await session.scalar(select(func.max(FAQ.display_order)).where(FAQ.bot_id == bot_id)) or 0
        faq = FAQ(bot_id=bot_id, question=question, answer=answer, display_order=max_order + 1)
        session.add(faq)
        await session.flush()
        await session.commit()
        return faq.id

async def update_faq(faq_id: int, bot_id: int, question: Optional[str] = None, answer: Optional[str] = None) -> bool:
    async with get_session() as session:
        faq = await session.scalar(select(FAQ).where(FAQ.id == faq_id, FAQ.bot_id == bot_id))
        if not faq:
            return False
        if question is not None:
            faq.question = question
        if answer is not None:
            faq.answer = answer
        await session.commit()
        return True

async def delete_faq(faq_id: int, bot_id: int) -> bool:
    async with get_session() as session:
        faq = await session.scalar(select(FAQ).where(FAQ.id == faq_id, FAQ.bot_id == bot_id))
        if not faq:
            return False
        await session.delete(faq)
        await session.commit()
        return True

async def get_faq(faq_id: int, bot_id: int) -> Optional[Dict[str, str]]:
    async with get_session() as session:
        faq = await session.scalar(select(FAQ).where(FAQ.id == faq_id, FAQ.bot_id == bot_id))
        if not faq:
            return None
        return {"id": faq.id, "question": faq.question, "answer": faq.answer}

async def list_faqs(bot_id: int) -> List[Dict[str, str]]:
    async with get_session() as session:
        stmt = select(FAQ).where(FAQ.bot_id == bot_id).order_by(FAQ.display_order)
        result = await session.execute(stmt)
        return [{"id": f.id, "question": f.question, "answer": f.answer} for f in result.scalars()]