"""
Motor de Webhooks para notificar a clientes cuando una auditoría se complete
"""
from supabase import create_client, Client
import os
from utils.webhook_utils import send_webhook
import asyncio

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

async def trigger_audit_completed_webhooks(user_id: str, audit_id: str, payload: dict):
    if not supabase:
        return
    res = supabase.table("webhooks").select("url").eq("user_id", user_id).eq("event", "audit.completed").eq("is_active", True).execute()
    if not res or not res.data:
        return
    for wh in res.data:
        await send_webhook(wh["url"], {"audit_id": audit_id, **payload})
