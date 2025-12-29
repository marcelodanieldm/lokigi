"""
Retargeting Engine para Lokigi
Automatización de Mensajería y Colas (FastAPI + Supabase Edge Functions)

- Programa 3 impactos de seguimiento tras la generación de un lead:
  - T+1h: Email/WA con PDF del reporte.
  - T+24h: Email/WA con cupón de descuento dinámico.
  - T+7d: Email/WA con testimonio de éxito.
- Cancela el flujo si se recibe un webhook de compra exitosa (Stripe checkout.session.completed).
- Usa Supabase Edge Functions para scheduling (o Upstash Redis si se requiere).
- Integra SendGrid (email) y Twilio (WhatsApp).
"""
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from datetime import datetime, timedelta
import requests
import os
import supabase

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM")

# Simulación de cola en Supabase (puede usarse Upstash Redis en producción)
def schedule_followup(user_id: str, impact_type: str, send_at: datetime, payload: dict):
    # Insertar en tabla 'followup_queue' de Supabase
    client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
    client.table('followup_queue').insert({
        "user_id": user_id,
        "impact_type": impact_type,
        "send_at": send_at.isoformat(),
        "payload": payload,
        "status": "pending"
    }).execute()

# Envío de email vía SendGrid
def send_email(to_email: str, subject: str, content: str, attachment_url: str = None):
    data = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": "noreply@lokigi.com"},
        "subject": subject,
        "content": [{"type": "text/html", "value": content}]
    }
    if attachment_url:
        # Adjuntar PDF como link (para capa gratuita)
        data["content"][0]["value"] += f'<br><a href="{attachment_url}">Descargar reporte PDF</a>'
    resp = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}", "Content-Type": "application/json"},
        json=data
    )
    return resp.status_code == 202

# Envío de WhatsApp vía Twilio
def send_whatsapp(to_number: str, message: str):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    data = {
        "From": f"whatsapp:{TWILIO_FROM}",
        "To": f"whatsapp:{to_number}",
        "Body": message
    }
    resp = requests.post(url, data=data, auth=(TWILIO_SID, TWILIO_TOKEN))
    return resp.status_code == 201

@router.post("/retargeting/schedule")
def schedule_retargeting(user_id: str, email: str, phone: str, pdf_url: str, coupon_code: str, testimonial: str, background_tasks: BackgroundTasks):
    now = datetime.utcnow()
    # T+1h: PDF
    schedule_followup(user_id, "pdf", now + timedelta(hours=1), {"email": email, "phone": phone, "pdf_url": pdf_url})
    # T+24h: Cupón
    schedule_followup(user_id, "coupon", now + timedelta(hours=24), {"email": email, "phone": phone, "coupon_code": coupon_code})
    # T+7d: Testimonio
    schedule_followup(user_id, "testimonial", now + timedelta(days=7), {"email": email, "phone": phone, "testimonial": testimonial})
    return {"status": "scheduled"}

@router.post("/retargeting/cancel")
def cancel_retargeting(user_id: str):
    # Marca como cancelados los followups pendientes
    client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
    client.table('followup_queue').update({"status": "cancelled"}).eq("user_id", user_id).eq("status", "pending").execute()
    return {"status": "cancelled"}

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    event = await request.json()
    if event.get("type") == "checkout.session.completed":
        user_id = event["data"]["object"].get("client_reference_id")
        if user_id:
            cancel_retargeting(user_id)
    return {"received": True}

# Edge Function/Worker (ejecutar cada minuto)
def process_followup_queue():
    client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
    now = datetime.utcnow().isoformat()
    rows = client.table('followup_queue').select('*').eq('status', 'pending').lte('send_at', now).execute().data
    for row in rows:
        if row['impact_type'] == 'pdf':
            send_email(row['payload']['email'], "Tu reporte Lokigi", "Adjuntamos tu reporte PDF.", row['payload']['pdf_url'])
            send_whatsapp(row['payload']['phone'], "¡Aquí tienes tu reporte PDF de Lokigi! " + row['payload']['pdf_url'])
        elif row['impact_type'] == 'coupon':
            send_email(row['payload']['email'], "Cupón de descuento Lokigi", f"¡15% de descuento solo por 4h! Código: {row['payload']['coupon_code']}", None)
            send_whatsapp(row['payload']['phone'], f"¡15% de descuento solo por 4h! Código: {row['payload']['coupon_code']}")
        elif row['impact_type'] == 'testimonial':
            send_email(row['payload']['email'], "Historias de éxito Lokigi", row['payload']['testimonial'], None)
            send_whatsapp(row['payload']['phone'], row['payload']['testimonial'])
        # Marcar como enviado
        client.table('followup_queue').update({"status": "sent"}).eq('id', row['id']).execute()

# Documentación:
# - Llama /retargeting/schedule al generar un lead.
# - Llama /retargeting/cancel o espera webhook Stripe para cancelar.
# - Ejecuta process_followup_queue() como Edge Function/cron cada minuto.
# - Configura las variables de entorno y tablas necesarias en Supabase.
# - Personaliza los mensajes y adjuntos según el flujo de negocio.
