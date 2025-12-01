import httpx
import logging
import re

logger = logging.getLogger(__name__)

async def get_bcv_rate():
    """
    Obtiene la tasa del dólar BCV.
    Intenta varias fuentes en orden.
    Retorna float o None si falla.
    """
    # 1. Intentar API de pydolarvenezuela (versión Vercel)
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("https://pydolarvenezuela-api.vercel.app/api/v1/dollar?page=bcv")
            if response.status_code == 200:
                data = response.json()
                # La estructura suele ser {'monitors': {'usd': {'price': 36.23}}}
                # O a veces cambia, hay que ser defensivos
                if 'monitors' in data and 'usd' in data['monitors']:
                    return float(data['monitors']['usd']['price'])
    except Exception as e:
        logger.warning(f"Fallo obteniendo tasa BCV de API 1: {e}")

    # 2. Intentar scraping directo simple (fallback)
    # Nota: BCV suele bloquear o tener SSL malo, así que esto es último recurso
    # O usar otra API pública si existe.
    
    # Por ahora retornamos None para que el handler pida ingreso manual o use tasa fija si se desea
    return None
