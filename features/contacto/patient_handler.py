from telegram import Update
from telegram.ext import ContextTypes
import html

from config import DB_PATH
from database.session import get_session
from database.repositories.contact_repository import ContactRepository
from utils.role_manager import RoleManager
from .keyboards import get_patient_contact_keyboard

role_manager = RoleManager(DB_PATH)


async def show_patient_contact(update: Update, context: ContextTypes.DEFAULT_TYPE, doctor_id: int):
    """Muestra solo el enlace de WhatsApp del médico asignado (independiente por inquilino)."""
    query = update.callback_query
    await query.answer()

    doctor = await role_manager.get_doctor_by_id(doctor_id)
    async with get_session() as session:
        contact_repo = ContactRepository(session)
        contact = await contact_repo.get_contact(doctor_id)
        
        if not doctor or not contact:
            message = "Puedes contactarme via Whatsapp a traves de este enlace http://wa.me/580000000000"
        else:
            wa_raw = (contact.get("whatsapp") or "").strip()
            if not wa_raw:
                message = "Puedes contactarme via Whatsapp a traves de este enlace http://wa.me/580000000000"
            else:
                # Si es número, normalizamos a wa.me; si ya es link, lo usamos tal cual
                if wa_raw.startswith("http://") or wa_raw.startswith("https://"):
                    wa_link = wa_raw
                else:
                    digits = "".join(ch for ch in wa_raw if ch.isdigit())
                    wa_link = f"http://wa.me/{digits}" if digits else wa_raw
                message = f"Puedes contactarme via Whatsapp a traves de este enlace {html.escape(wa_link)}"

        await query.edit_message_text(
            message,
            reply_markup=get_patient_contact_keyboard(),
            parse_mode="HTML",
        )
