"""
Utilidades de inicio del bot
"""
import asyncio
from database.session import get_session
from database.repositories.user_repository import DoctorRepository
from config import DB_PATH


async def cleanup_on_start_async():
    """
    Limpia asociaciones incorrectas de doctores y pacientes al iniciar
    """
    async with get_session() as session:
        repo = DoctorRepository(session)
        cleaned = await repo.cleanup_doctor_patient_associations()
        if cleaned > 0:
            print(f"🧹 Limpiadas {cleaned} asociaciones incorrectas al iniciar")
        return cleaned


def cleanup_on_start():
    """
    Limpia asociaciones incorrectas de doctores y pacientes al iniciar (wrapper síncrono)
    """
    try:
        loop = asyncio.get_running_loop()
        # Si hay un loop corriendo, ejecutar en un thread separado
        future = asyncio.run_coroutine_threadsafe(cleanup_on_start_async(), loop)
        return future.result()
    except RuntimeError:
        # No hay loop corriendo, podemos usar asyncio.run()
        return asyncio.run(cleanup_on_start_async())
