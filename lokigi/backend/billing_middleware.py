"""
Middleware y utilidades para facturación por exceso de créditos (Stripe Overage Billing)
"""
from fastapi import Request, HTTPException
from supabase import create_client, Client
import os
import stripe

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

CREDIT_COST = 0.05  # USD por crédito extra

async def check_and_bill_overage(api_key: str):
    if not supabase:
        return
    # Buscar api_key_id y user_id
    from utils.api_key_utils import hash_api_key
    key_hash = hash_api_key(api_key)
    res = supabase.table("api_keys").select("id, user_id").eq("key_hash", key_hash).eq("is_active", True).single().execute()
    if not res or not res.data:
        raise HTTPException(status_code=401, detail="API Key inválida")
    api_key_id = res.data["id"]
    user_id = res.data["user_id"]
    # Buscar créditos usados
    credits = supabase.table("api_credits").select("id, credits_used, credits_limit, period_start, period_end").eq("api_key_id", api_key_id).single().execute()
    if not credits or not credits.data:
        # Crear registro si no existe
        supabase.table("api_credits").insert({"api_key_id": api_key_id, "user_id": user_id, "credits_used": 1}).execute()
        return
    credits_used = credits.data["credits_used"] + 1
    credits_limit = credits.data["credits_limit"]
    # Actualizar uso
    supabase.table("api_credits").update({"credits_used": credits_used}).eq("id", credits.data["id"]).execute()
    # Si excede el límite, facturar
    if credits_used > credits_limit:
        # Buscar Stripe customer_id
        user = supabase.table("users").select("stripe_customer_id").eq("id", user_id).single().execute()
        if not user or not user.data or not user.data.get("stripe_customer_id"):
            raise HTTPException(status_code=402, detail="No Stripe customer_id")
        customer_id = user.data["stripe_customer_id"]
        amount = int(CREDIT_COST * 100)  # en centavos
        invoice = stripe.Invoice.create(
            customer=customer_id,
            auto_advance=True,
            collection_method="charge_automatically",
            description="Lokigi API Overage Credit",
            metadata={"api_key_id": api_key_id}
        )
        stripe.InvoiceItem.create(
            customer=customer_id,
            amount=amount,
            currency="usd",
            invoice=invoice.id,
            description="1 crédito extra API"
        )
        supabase.table("api_billing_events").insert({
            "api_key_id": api_key_id,
            "user_id": user_id,
            "credits_billed": 1,
            "amount": CREDIT_COST,
            "currency": "USD",
            "stripe_invoice_id": invoice.id
        }).execute()
