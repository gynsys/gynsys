# database/connection.py
import aiosqlite
import logging
from config import DATABASE_NAME

logger = logging.getLogger(__name__)

async def get_db_connection():
    try:
        conn = await aiosqlite.connect(DATABASE_NAME, timeout=10)
        await conn.execute("PRAGMA foreign_keys = ON;")
        await conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = aiosqlite.Row
        return conn
    except aiosqlite.Error as e:
        logger.error(f"Error de base de datos al conectar: {e}", exc_info=True)
        return None

async def init_db():
    conn = await get_db_connection()
    if not conn: return
    try:
        # --- SCRIPT ÚNICO Y COMPLETO PARA CREAR TODAS LAS TABLAS ---
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS medical_histories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id INTEGER,
                bot_id INTEGER,
                user_id INTEGER NOT NULL,
                history_number TEXT,
                full_name TEXT,
                age TEXT,
                ci TEXT,
                phone TEXT,
                address TEXT,
                occupation TEXT,
                family_history_mother TEXT,
                family_history_father TEXT,
                personal_history TEXT,
                supplements TEXT,
                surgical_history TEXT,
                gyn_menarche TEXT,
                gyn_ho TEXT,
                gyn_cycles TEXT,
                gyn_fertility_intent TEXT,
                gyn_dysmenorrhea TEXT,
                gyn_sexarche TEXT,
                sexually_active TEXT,
                gyn_fum TEXT,
                gyn_mac TEXT,
                gyn_previous_checkups TEXT,
                gyn_last_pap_smear TEXT,
                leg_pain_type TEXT,
                leg_pain_zone TEXT,
                sexual_pain_dyspareunia TEXT,
                sexual_pain_type TEXT,
                sexual_pain_scale TEXT,
                habits_smoking TEXT,
                habits_alcohol TEXT,
                gastro_symptoms_before_period TEXT,
                gastro_symptoms_during_period TEXT,
                bowel_dischezia TEXT,
                bowel_dischezia_scale TEXT,
                bowel_frequency TEXT,
                habits_urinary TEXT,
                urinary_pain_scale TEXT,
                urinary_irritation TEXT,
                urinary_incontinence TEXT,
                urinary_nocturia TEXT,
                functional_dispareunia TEXT,
                functional_leg_pain TEXT,
                functional_gastro_before TEXT,
                functional_gastro_during TEXT,
                functional_dischezia TEXT,
                functional_bowel_freq TEXT,
                functional_urinary_problem TEXT,
                functional_urinary_pain TEXT,
                functional_urinary_irritation TEXT,
                functional_urinary_incontinence TEXT,
                functional_urinary_nocturia TEXT,
                habits_physical_activity TEXT,
                habits_substance_use TEXT,
                summary_functional_exam TEXT,
                summary_gyn_obstetric TEXT,
                summary_habits TEXT,
                consultation_type TEXT,
                reason_for_visit TEXT,
                prenatal_details TEXT,
                admin_physical_exam TEXT,
                admin_ultrasound TEXT,
                admin_diagnosis TEXT,
                admin_plan TEXT,
                admin_observations TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS bots (id INTEGER PRIMARY KEY AUTOINCREMENT, doctor_name TEXT NOT NULL, token TEXT NOT NULL UNIQUE, admin_user_id INTEGER NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS text_content (key TEXT NOT NULL, value TEXT NOT NULL, bot_id INTEGER NOT NULL, PRIMARY KEY (key, bot_id), FOREIGN KEY (bot_id) REFERENCES bots (id));
            CREATE TABLE IF NOT EXISTS locations (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id INTEGER NOT NULL, name TEXT NOT NULL, address TEXT NOT NULL, schedule TEXT, Maps_url TEXT, is_active BOOLEAN NOT NULL DEFAULT 1, display_order INTEGER DEFAULT 0, FOREIGN KEY (bot_id) REFERENCES bots (id));
            CREATE TABLE IF NOT EXISTS citas (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id INTEGER NOT NULL, user_id INTEGER NOT NULL, user_name TEXT, phone TEXT, reason TEXT, fecha TEXT NOT NULL, hora TEXT NOT NULL, ubicacion TEXT NOT NULL, status TEXT DEFAULT 'pending', reminder_sent BOOLEAN NOT NULL DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (bot_id) REFERENCES bots (id));
            CREATE TABLE IF NOT EXISTS user_actions (user_id INTEGER NOT NULL, bot_id INTEGER NOT NULL, action_key TEXT NOT NULL, timestamp INTEGER NOT NULL, PRIMARY KEY (user_id, bot_id, action_key));
            CREATE TABLE IF NOT EXISTS faqs (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id INTEGER NOT NULL, question TEXT NOT NULL, answer TEXT NOT NULL, display_order INTEGER DEFAULT 0, FOREIGN KEY (bot_id) REFERENCES bots (id));
            CREATE TABLE IF NOT EXISTS consejos (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id INTEGER NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL, display_order INTEGER DEFAULT 0, FOREIGN KEY (bot_id) REFERENCES bots (id));
            CREATE TABLE IF NOT EXISTS gallery (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id INTEGER NOT NULL, title TEXT NOT NULL, content TEXT, media_file_id TEXT, media_type TEXT, display_order INTEGER DEFAULT 0, FOREIGN KEY (bot_id) REFERENCES bots (id));
            CREATE TABLE IF NOT EXISTS diagnosticos (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id INTEGER NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL, image_file_id TEXT, display_order INTEGER DEFAULT 0, FOREIGN KEY (bot_id) REFERENCES bots (id));
            CREATE TABLE IF NOT EXISTS precios (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id INTEGER NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL, display_order INTEGER DEFAULT 0, FOREIGN KEY (bot_id) REFERENCES bots (id));
            CREATE TABLE IF NOT EXISTS main_menu_buttons (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id INTEGER NOT NULL, text TEXT NOT NULL, callback_data TEXT NOT NULL, row_number INTEGER NOT NULL, display_order INTEGER NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1, FOREIGN KEY (bot_id) REFERENCES bots (id));
            CREATE TABLE IF NOT EXISTS test_questions (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id INTEGER NOT NULL, question TEXT NOT NULL, display_order INTEGER DEFAULT 0, FOREIGN KEY (bot_id) REFERENCES bots (id));
            CREATE TABLE IF NOT EXISTS submenus (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id INTEGER NOT NULL, name TEXT NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1, display_order INTEGER DEFAULT 0, FOREIGN KEY (bot_id) REFERENCES bots (id));
            CREATE TABLE IF NOT EXISTS submenu_buttons (id INTEGER PRIMARY KEY AUTOINCREMENT, submenu_id INTEGER NOT NULL, text TEXT NOT NULL, callback_data TEXT NOT NULL, row_number INTEGER NOT NULL, display_order INTEGER NOT NULL, is_active BOOLEAN NOT NULL DEFAULT 1, FOREIGN KEY (submenu_id) REFERENCES submenus (id) ON DELETE CASCADE);
            CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT, bot_id INTEGER NOT NULL, user_id INTEGER NOT NULL, message TEXT, notification_type TEXT, is_read BOOLEAN DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
            CREATE INDEX IF NOT EXISTS idx_citas_reminder ON citas (bot_id, status, reminder_sent);
            CREATE INDEX IF NOT EXISTS idx_citas_fecha_status ON citas (bot_id, fecha, status);
            CREATE INDEX IF NOT EXISTS idx_citas_usuario_activo ON citas (user_id, bot_id, status);
            CREATE TABLE IF NOT EXISTS bot_logos (
                bot_id INTEGER PRIMARY KEY,
                logo_header_1 TEXT,
                logo_header_2 TEXT,
                logo_signature TEXT,
                FOREIGN KEY (bot_id) REFERENCES bots (id) ON DELETE CASCADE
            );

            -- TABLA: Configuración de PDF (Multi-tenant: usa doctor_id)
            CREATE TABLE IF NOT EXISTS pdf_settings (
                doctor_id INTEGER NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT,
                is_visible BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (doctor_id, setting_key)
            );

            -- TABLA: Módulos extras por doctor (funcionalidades adicionales)
            CREATE TABLE IF NOT EXISTS extra_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id INTEGER NOT NULL,
                module_name TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(doctor_id, module_name),
                FOREIGN KEY (doctor_id) REFERENCES doctors (id) ON DELETE CASCADE
            );

        """)

        # Script de migración para añadir columnas si faltan (más seguro)
        cursor = await conn.execute("PRAGMA table_info(medical_histories)")
        columns = [row['name'] for row in await cursor.fetchall()]

        if 'prenatal_details' not in columns:
            await conn.execute('ALTER TABLE medical_histories ADD COLUMN prenatal_details TEXT;')
            logger.info("MIGRACIÓN: Columna 'prenatal_details' añadida a 'medical_histories'.")

        # Migración: Si pdf_settings existe con bot_id, crear nueva tabla con doctor_id
        # (SQLite no soporta ALTER COLUMN, así que creamos una nueva estructura)
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdf_settings'")
        if await cursor.fetchone():
            # Verificar si tiene bot_id o doctor_id
            cursor = await conn.execute("PRAGMA table_info(pdf_settings)")
            pdf_columns = [row['name'] for row in await cursor.fetchall()]
            
            if 'bot_id' in pdf_columns and 'doctor_id' not in pdf_columns:
                # Migrar datos de bot_id a doctor_id (asumiendo que bot_id = doctor_id en el nuevo sistema)
                logger.info("MIGRACIÓN: Migrando pdf_settings de bot_id a doctor_id...")
                try:
                    # Crear tabla temporal
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS pdf_settings_new (
                            doctor_id INTEGER NOT NULL,
                            setting_key TEXT NOT NULL,
                            setting_value TEXT,
                            is_visible BOOLEAN DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            PRIMARY KEY (doctor_id, setting_key)
                        )
                    """)
                    # Copiar datos (asumiendo que bot_id puede mapearse a doctor_id)
                    await conn.execute("""
                        INSERT OR IGNORE INTO pdf_settings_new (doctor_id, setting_key, setting_value, is_visible, created_at)
                        SELECT bot_id, setting_key, setting_value, is_visible, created_at
                        FROM pdf_settings
                    """)
                    # Eliminar tabla vieja
                    await conn.execute("DROP TABLE pdf_settings")
                    # Renombrar nueva tabla
                    await conn.execute("ALTER TABLE pdf_settings_new RENAME TO pdf_settings")
                    logger.info("MIGRACIÓN: pdf_settings migrado exitosamente a doctor_id.")
                except Exception as e:
                    logger.warning(f"MIGRACIÓN: Error migrando pdf_settings, se creará nueva estructura: {e}")
                    # Si falla, simplemente se creará la nueva estructura en el siguiente init_db

        await conn.commit()
        logger.info("Base de datos inicializada/verificada correctamente.")
    except aiosqlite.Error as e:
        logger.error(f"Error al inicializar la base de datos: {e}", exc_info=True)
    finally:
        if conn: await conn.close()