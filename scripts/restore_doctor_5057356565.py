import sqlite3
import os
import sys

# Add project root to path to allow importing config if needed, 
# though we are using direct sqlite3 here for simplicity.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH

def restore_data():
    print(f"🔌 Conectando a la base de datos en: {DB_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Restaurar Doctor
        print("Restaurando doctor...")
        try:
            cursor.execute("""
                INSERT INTO doctors (id, name, telegram_id, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (1, 'maariel2', 5057356565, 1, '2025-11-23 19:17:22.564602'))
            print("✅ Doctor 'maariel2' restaurado (ID: 1)")
        except sqlite3.IntegrityError as e:
            print(f"⚠️ Error al restaurar doctor: {e}")

        # 2. Restaurar Bot
        print("Restaurando configuración del bot...")
        try:
            cursor.execute("""
                INSERT INTO bots (id, doctor_name, token, admin_user_id, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (4, 'maariel2', 'tenant_1_placeholder', 5057356565, 1))
            print("✅ Bot restaurado (ID: 4)")
        except sqlite3.IntegrityError as e:
            print(f"⚠️ Error al restaurar bot: {e}")

        # 3. Restaurar relación User-Tenant
        print("Restaurando relación usuario-inquilino...")
        try:
            cursor.execute("""
                INSERT INTO user_tenants (id, user_id, bot_id)
                VALUES (?, ?, ?)
            """, (1, 5057356565, 4))
            print("✅ Relación User-Tenant restaurada")
        except sqlite3.IntegrityError as e:
            print(f"⚠️ Error al restaurar user_tenant: {e}")

        conn.commit()
        conn.close()
        print("\n🎉 Proceso completado exitosamente.")
        
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")

if __name__ == "__main__":
    restore_data()
