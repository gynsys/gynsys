import logging
import asyncio
import datetime
import os
import glob
from config import SUPER_ADMIN_ID
from telegram.ext import Application, ContextTypes
from backup import main as perform_backup

logger = logging.getLogger(__name__)

async def scheduled_db_backup(context: ContextTypes.DEFAULT_TYPE):
    """
    Ejecuta el script de backup de forma asíncrona.
    Se manda al event loop para no bloquear el bot.
    """
    logger.info("Iniciando backup automático programado...")
    try:
        loop = asyncio.get_running_loop()
        # run_in_executor para ejecutar la función síncrona en un hilo separado
        result = await loop.run_in_executor(None, perform_backup)
        if result == 0:
            logger.info("✅ Backup automático completado exitosamente.")
            try:
                # Buscar el archivo más reciente en el directorio de backups
                backups = glob.glob('backups/*.db')
                if backups:
                    latest_backup = max(backups, key=os.path.getctime)
                    with open(latest_backup, 'rb') as f:
                        await context.bot.send_document(
                            chat_id=SUPER_ADMIN_ID,
                            document=f,
                            caption="✅ Backup automático diario de la base de datos."
                        )
                        logger.info("✅ Backup enviado por Telegram al administrador.")
                else:
                    logger.warning("No se encontraron archivos de backup para enviar por Telegram.")
            except Exception as e:
                logger.error(f"Error enviando el archivo de backup por Telegram: {e}")
        else:
            logger.error("❌ El backup automático reportó un fallo (exit code 1).")
    except Exception as e:
        logger.error(f"Error ejecutando el backup automático: {e}", exc_info=True)


def setup_jobs(application: Application):
    """
    Configura todos los trabajos programados (cron jobs) del bot.
    """
    job_queue = application.job_queue
    if not job_queue:
        logger.error("⚠️ El JobQueue no está inicializado. Asegúrate de tener APScheduler instalado.")
        return
        
    import pytz
    tz = pytz.timezone('America/Caracas')
        
    # 1. Programar el backup diario a las 8:20 AM (temporal para pruebas)
    backup_time = datetime.time(hour=9, minute=30, second=0, tzinfo=tz)
    job_queue.run_daily(
        scheduled_db_backup,
        time=backup_time,
        name="daily_db_backup"
    )
    logger.info(f"✅ Trabajo programado 'daily_db_backup' configurado para las {backup_time.strftime('%H:%M:%S')} diariamente.")

    # 2. Programar los recordatorios de citas
    from utils.reminder_service import send_daily_reminders
    
    # Mañana: 7:00 AM
    morning_time = datetime.time(hour=7, minute=0, second=0, tzinfo=tz)
    job_queue.run_daily(
        send_daily_reminders,
        time=morning_time,
        name="morning_appointment_reminders"
    )
    logger.info(f"✅ Recordatorio mañana configurado para las {morning_time.strftime('%H:%M:%S')} diariamente.")
    
    # Tarde: 1:00 PM (13:00)
    afternoon_time = datetime.time(hour=13, minute=0, second=0, tzinfo=tz)
    job_queue.run_daily(
        send_daily_reminders,
        time=afternoon_time,
        name="afternoon_appointment_reminders"
    )
    logger.info(f"✅ Recordatorio tarde configurado para las {afternoon_time.strftime('%H:%M:%S')} diariamente.")
