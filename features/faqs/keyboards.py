"""
Teclados para FAQs – refactor multi-tenant.
Mismo nombre de archivo para no romper imports.
"""
from telegram import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM
from typing import List, Dict

async def faqs_for_action_keyboard(items: List[Dict[str, str]], action: str) -> IKM:
    emoji = "✏️" if action == "modify" else "🗑️"
    buttons = [
        [IKB(f"{emoji} {item['question']}", callback_data=f"faq_{action}_{item['id']}")]
        for item in items
    ]
    buttons.append([IKB("🔙 Volver", callback_data="faqs_admin_hub")])
    return IKM(buttons)

async def faq_user_keyboard(items: List[Dict[str, str]]) -> IKM:
    buttons = [
        [IKB(item["question"], callback_data=f"faq_view_{item['id']}")]
        for item in items
    ]
    buttons.append([IKB("🏠 Menú Principal", callback_data="main_menu")])
    return IKM(buttons)