import stripe
import os
from typing import Optional
from sqlalchemy.orm import Session
from models import Lead, PaymentStatus
from datetime import datetime

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


def create_checkout_session(
    lead: Lead,
    success_url: str,
    cancel_url: str
) -> dict:
    """
    Crea una sesión de checkout en Stripe para el Plan Express
    """
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': 900,  # $9.00 en centavos
                    'product_data': {
                        'name': 'Plan de Acción Express',
                        'description': 'PDF personalizado con plan de acción para mejorar tu SEO Local',
                        'images': ['https://lokigi.com/plan-express.png'],  # Reemplazar con imagen real
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=lead.email,
            metadata={
                'lead_id': str(lead.id),
                'business_name': lead.nombre_negocio,
            },
            client_reference_id=str(lead.id),
        )
        
        return {
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id,
        }
    except Exception as e:
        raise Exception(f"Error al crear sesión de Stripe: {str(e)}")


def handle_webhook_event(
    payload: bytes,
    sig_header: str,
    db: Session
) -> dict:
    """
    Procesa eventos del webhook de Stripe
    """
    try:
        # Verificar la firma del webhook
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise ValueError("Payload inválido")
    except stripe.error.SignatureVerificationError as e:
        raise ValueError("Firma inválida")

    # Manejar el evento
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        return handle_successful_payment(session, db)
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        return handle_failed_payment(payment_intent, db)

    return {'status': 'unhandled_event', 'type': event['type']}


def handle_successful_payment(session: dict, db: Session) -> dict:
    """
    Maneja un pago exitoso
    """
    lead_id = session.get('client_reference_id')
    
    if not lead_id:
        return {'status': 'error', 'message': 'No lead_id found'}
    
    lead = db.query(Lead).filter(Lead.id == int(lead_id)).first()
    
    if not lead:
        return {'status': 'error', 'message': 'Lead not found'}
    
    # Actualizar el lead
    lead.payment_status = PaymentStatus.PAID
    lead.stripe_checkout_session_id = session['id']
    lead.stripe_payment_intent_id = session.get('payment_intent')
    lead.paid_at = datetime.utcnow()
    lead.plan_express_accepted = True
    
    db.commit()
    
    # Aquí podrías disparar:
    # - Email de confirmación
    # - Generación del PDF
    # - Notificación al equipo
    
    return {
        'status': 'success',
        'lead_id': lead_id,
        'message': 'Payment processed successfully'
    }


def handle_failed_payment(payment_intent: dict, db: Session) -> dict:
    """
    Maneja un pago fallido
    """
    # Buscar el lead por el payment_intent_id
    lead = db.query(Lead).filter(
        Lead.stripe_payment_intent_id == payment_intent['id']
    ).first()
    
    if lead:
        lead.payment_status = PaymentStatus.FAILED
        db.commit()
        return {'status': 'payment_failed', 'lead_id': lead.id}
    
    return {'status': 'error', 'message': 'Lead not found'}


def mark_as_delivered(lead_id: int, db: Session) -> Lead:
    """
    Marca un lead como entregado (después de enviar el PDF)
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    
    if not lead:
        raise ValueError("Lead not found")
    
    if lead.payment_status != PaymentStatus.PAID:
        raise ValueError("Payment not completed")
    
    lead.payment_status = PaymentStatus.DELIVERED
    lead.delivered_at = datetime.utcnow()
    db.commit()
    
    return lead
