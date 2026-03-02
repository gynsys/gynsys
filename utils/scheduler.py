import logging
import asyncio
import datetime
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
        
    # Programar el backup diario a las 3:00 AM (hora local del servidor)
    target_time = datetime.time(hour=3, minute=0, second=0)
    
    # Agregar el job
    job_queue.run_daily(
        scheduled_db_backup,
        time=target_time,
        name="daily_db_backup"
    )
    
    logger.info(f"✅ Trabajo programado 'daily_db_backup' configurado para las {target_time.strftime('%H:%M:%S')} diariamente.")
