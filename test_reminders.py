import asyncio
import logging
from utils.reminder_service import send_daily_reminders

logging.basicConfig(level=logging.INFO)

# Mock context
class MockBot:
    async def send_message(self, chat_id, text, parse_mode=None):
        print(f"\n--- ENVIANDO A CHAT {chat_id} ---")
        print(text)
        print("----------------------------------\n")

class MockContext:
    def __init__(self):
        self.bot = MockBot()

async def test():
    context = MockContext()
    await send_daily_reminders(context)

if __name__ == "__main__":
    asyncio.run(test())
