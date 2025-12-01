import httpx
import logging
from pyDolarVenezuela.pages import BCV
from pyDolarVenezuela import Monitor

logger = logging.getLogger(__name__)

async def get_bcv_rate():
    """
    Obtiene la tasa del dólar BCV usando la librería pyDolarVenezuela.
    Retorna float o None si falla.
    """
    try:
        # Usar la librería oficial que es más robusta
        monitor = Monitor(BCV)
        data = monitor.get_value_monitors("usd")
        if data and hasattr(data, 'price'):
            return float(data.price)
    except Exception as e:
        logger.warning(f"Fallo obteniendo tasa BCV con librería: {e}")

    # Fallback a API si la librería falla
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("https://pydolarvenezuela-api.vercel.app/api/v1/dollar?page=bcv")
            if response.status_code == 200:
                data = response.json()
                if 'monitors' in data and 'usd' in data['monitors']:
                    return float(data['monitors']['usd']['price'])
    except Exception as e:
        logger.warning(f"Fallo obteniendo tasa BCV de API fallback: {e}")
    
    return None
    return None
