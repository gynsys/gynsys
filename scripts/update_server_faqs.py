import asyncio
import logging
from sqlalchemy import select
from database.session import get_session
from database.models.content import FAQ

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FAQS_DATA = [
    {'bot_id': 4, 'question': '¿Cuáles son los horarios de atención?', 'answer': "Los horarios de atención están disponibles en la sección '📍 Ubicaciones' del menú principal. Allí encontrarás toda la información sobre nuestros horarios y ubicaciones.", 'display_order': 2},
    {'bot_id': 4, 'question': '¿Cómo puedo contactar directamente?', 'answer': "Puedes contactarnos directamente a través del botón '📞 Contacto' en el menú principal, donde encontrarás nuestros números de teléfono y canales de comunicación.", 'display_order': 3},
    {'bot_id': 4, 'question': '¿Dónde están ubicadas las consultas?', 'answer': "Nuestras ubicaciones están disponibles en la sección '📍 Ubicaciones' del menú principal. Allí encontrarás direcciones, mapas y horarios de cada consultorio.", 'display_order': 4},
    {'bot_id': 4, 'question': '¿Cuáles son los precios de las consultas?', 'answer': "Los precios de nuestras consultas y servicios están disponibles en la sección '💰 Precios' del menú principal. Puedes consultar los costos de cada tipo de consulta.", 'display_order': 5},
    {'bot_id': 5, 'question': '¿Cómo puedo agendar una cita?', 'answer': "Puedes agendar una cita presionando el botón '📅 Citas' en el menú principal. Selecciona la fecha y hora que mejor se adapte a tu disponibilidad.", 'display_order': 1},
    {'bot_id': 5, 'question': '¿Cuáles son los horarios de atención?', 'answer': "Los horarios de atención están disponibles en la sección '📍 Ubicaciones' del menú principal. Allí encontrarás toda la información sobre nuestros horarios y ubicaciones.", 'display_order': 2},
    {'bot_id': 5, 'question': '¿Cómo puedo contactar directamente?', 'answer': "Puedes contactarnos directamente a través del botón '📞 Contacto' en el menú principal, donde encontrarás nuestros números de teléfono y canales de comunicación.", 'display_order': 3},
    {'bot_id': 5, 'question': '¿Dónde están ubicadas las consultas?', 'answer': "Nuestras ubicaciones están disponibles en la sección '📍 Ubicaciones' del menú principal. Allí encontrarás direcciones, mapas y horarios de cada consultorio.", 'display_order': 4},
    {'bot_id': 5, 'question': '¿Cuáles son los precios de las consultas?', 'answer': "Los precios de nuestras consultas y servicios están disponibles en la sección '💰 Precios' del menú principal. Puedes consultar los costos de cada tipo de consulta.", 'display_order': 5},
]

async def update_faqs():
    async with get_session() as session:
        for faq_data in FAQS_DATA:
            bot_id = faq_data['bot_id']
            question = faq_data['question']
            answer = faq_data['answer']
            display_order = faq_data['display_order']

            # Check if FAQ exists
            stmt = select(FAQ).where(FAQ.bot_id == bot_id, FAQ.question == question)
            result = await session.execute(stmt)
            existing_faq = result.scalar_one_or_none()

            if existing_faq:
                logger.info(f"Updating FAQ for bot {bot_id}: {question}")
                existing_faq.answer = answer
                existing_faq.display_order = display_order
            else:
                logger.info(f"Creating FAQ for bot {bot_id}: {question}")
                new_faq = FAQ(bot_id=bot_id, question=question, answer=answer, display_order=display_order)
                session.add(new_faq)
        
        await session.commit()
        logger.info("FAQs updated successfully.")

if __name__ == "__main__":
    asyncio.run(update_faqs())
