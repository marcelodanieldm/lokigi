import httpx
from typing import Dict

async def send_webhook(url: str, payload: Dict):
    """
    Envía un webhook asíncrono a la URL del cliente.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=10)
            return resp.status_code
        except Exception as e:
            return None
