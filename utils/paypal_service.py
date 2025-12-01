import httpx
import base64
import logging
from config import PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_API_URL

logger = logging.getLogger(__name__)

class PayPalService:
    def __init__(self):
        self.client_id = PAYPAL_CLIENT_ID
        self.client_secret = PAYPAL_CLIENT_SECRET
        self.api_url = PAYPAL_API_URL

    async def get_access_token(self):
        """Obtiene un token de acceso OAuth2 de PayPal"""
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.api_url}/v1/oauth2/token", headers=headers, data=data)
            response.raise_for_status()
            return response.json()["access_token"]

    async def create_order(self, amount: str, currency: str = "USD", return_url: str = "https://t.me/GynSysBot", cancel_url: str = "https://t.me/GynSysBot"):
        """Crea una orden de pago en PayPal"""
        try:
            token = await self.get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {
                        "currency_code": currency,
                        "value": amount
                    },
                    "description": "Suscripción Mensual GynSys Bot"
                }],
                "application_context": {
                    "brand_name": "GynSys",
                    "landing_page": "NO_PREFERENCE",
                    "user_action": "PAY_NOW",
                    "return_url": return_url,
                    "cancel_url": cancel_url
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{self.api_url}/v2/checkout/orders", headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error creando orden de PayPal: {e}")
            return None

    async def capture_order(self, order_id: str):
        """Captura el pago de una orden aprobada"""
        try:
            token = await self.get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/v2/checkout/orders/{order_id}/capture",
                    headers=headers
                )
                # Si ya fue capturada, PayPal devuelve 422 o similar, pero podemos consultar el estado
                if response.status_code != 201 and response.status_code != 200:
                    # Intentar obtener detalles si falló la captura (quizás ya estaba capturada)
                    details = await self.get_order_details(order_id)
                    return details
                
                return response.json()
        except Exception as e:
            logger.error(f"Error capturando orden {order_id}: {e}")
            return None

    async def get_order_details(self, order_id: str):
        """Obtiene los detalles de una orden"""
        try:
            token = await self.get_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.api_url}/v2/checkout/orders/{order_id}", headers=headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error obteniendo detalles de orden {order_id}: {e}")
            return None
