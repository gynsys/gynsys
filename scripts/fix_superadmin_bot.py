import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import get_session
from sqlalchemy import text
from config import SUPER_ADMIN_ID, BOT_TOKEN

async def fix_superadmin_bot():
    if not SUPER_ADMIN_ID:
        print("❌ SUPER_ADMIN_ID is not set in config/env!")
        return

    async with get_session() as session:
        # Check if ID 1 exists
        result = await session.execute(text("SELECT id FROM bots WHERE id = 1"))
        if result.first():
            print("✅ Bot ID 1 already exists.")
            return

        print(f"🔧 Creating Bot ID 1 for SuperAdmin (ID: {SUPER_ADMIN_ID})...")
        
        # Insert Bot ID 1
        # We use a placeholder token if BOT_TOKEN is used for the main bot
        # Or we can use the actual BOT_TOKEN if this IS the main bot entry
        
        try:
            await session.execute(text("""
                INSERT INTO bots (id, doctor_name, token, admin_user_id, is_active)
                VALUES (1, 'GynSys Main Bot', :token, :admin_id, 1)
            """), {
                'token': BOT_TOKEN,
                'admin_id': SUPER_ADMIN_ID
            })
            await session.commit()
            print("✅ Bot ID 1 created successfully!")
        except Exception as e:
            print(f"❌ Error creating bot: {e}")
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(fix_superadmin_bot())
