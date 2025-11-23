import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).resolve().parents[2] / "database" / "medical_bot.db"


def delete_doctor_by_telegram_id(telegram_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM doctors WHERE telegram_id = ?", (telegram_id,))
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    finally:
        conn.close()


def cleanup_patient_associations(telegram_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM patient_doctor
            WHERE doctor_id = (
                SELECT id FROM doctors WHERE telegram_id = ?
            )
            """,
            (telegram_id,),
        )
        removed = cur.rowcount
        conn.commit()
        return removed
    finally:
        conn.close()


def main():
    telegram_id = int(input("Ingresa el Telegram ID del médico a eliminar: ").strip())

    removed_doctor = delete_doctor_by_telegram_id(telegram_id)
    removed_associations = cleanup_patient_associations(telegram_id)

    if removed_doctor:
        print(f"✅ Médico con Telegram ID {telegram_id} eliminado.")
    else:
        print(f"⚠️ No se encontró un médico con Telegram ID {telegram_id}.")

    if removed_associations:
        print(f"🧹 {removed_associations} asociaciones con pacientes eliminadas.")


if __name__ == "__main__":
    main()

