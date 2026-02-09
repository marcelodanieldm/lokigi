# backend/stripe_webhook.py
"""
Webhook de Stripe para actualizar el estado de suscripción en Supabase
"""
from fastapi import APIRouter, Request, Response
import stripe
import os
from supabase import create_client, Client

router = APIRouter()

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
supabase: Client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        return Response(f"Webhook error: {str(e)}", status_code=400)

    # Maneja eventos relevantes
    if event['type'] == 'invoice.payment_succeeded':
        user_id = event['data']['object']['metadata']['user_id']
        supabase.table('users').update({"subscription_status": "active"}).eq('id', user_id).execute()
    elif event['type'] == 'invoice.payment_failed':
        user_id = event['data']['object']['metadata']['user_id']
        supabase.table('users').update({"subscription_status": "past_due"}).eq('id', user_id).execute()
    elif event['type'] == 'customer.subscription.deleted':
        user_id = event['data']['object']['metadata']['user_id']
        supabase.table('users').update({"subscription_status": "canceled"}).eq('id', user_id).execute()

    return Response(status_code=200)
