"""
API de Pagos - Rutas para Stripe Checkout y Webhooks
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

from database import get_db
from models import Lead, Order, CustomerStatus
from stripe_payments import StripePaymentService

router = APIRouter(prefix="/api", tags=["payments"])


# Schemas
class LeadCreate(BaseModel):
    """Schema para crear un lead"""
    nombre: str
    email: EmailStr
    telefono: str
    whatsapp: Optional[str] = None
    nombre_negocio: str
    # Datos de auditoría (opcional al crear el lead)
    score_visibilidad: Optional[int] = None
    fallos_criticos: Optional[dict] = None
    audit_data: Optional[dict] = None


class CheckoutRequest(BaseModel):
    """Schema para solicitar checkout"""
    lead_id: int
    price_id: Optional[str] = None  # Opcional: ID de precio de Stripe (ej: price_1A2B3C4D5E6F)


class LeadResponse(BaseModel):
    """Schema de respuesta de lead"""
    id: int
    nombre: str
    email: str
    telefono: str
    whatsapp: Optional[str]
    nombre_negocio: str
    customer_status: str
    score_visibilidad: Optional[int]
    
    class Config:
        from_attributes = True


# Endpoints de Leads
@router.post("/leads", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(lead: LeadCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo lead en la base de datos
    Este endpoint se llama cuando el usuario completa el formulario modal
    """
    # Verificar si el email ya existe
    existing_lead = db.query(Lead).filter(Lead.email == lead.email).first()
    if existing_lead:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este email ya está registrado"
        )
    
    # Crear el lead
    db_lead = Lead(
        nombre=lead.nombre,
        email=lead.email,
        telefono=lead.telefono,
        whatsapp=lead.whatsapp or lead.telefono,
        nombre_negocio=lead.nombre_negocio,
        score_visibilidad=lead.score_visibilidad,
        fallos_criticos=lead.fallos_criticos,
        audit_data=lead.audit_data,
        customer_status=CustomerStatus.LEAD
    )
    
    db.add(db_lead)
    db.commit()
    db.refresh(db_lead)
    
    return db_lead


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """
    Obtiene información de un lead por su ID
    """
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead no encontrado"
        )
    return lead


# Endpoints de Checkout
@router.post("/create-checkout-session/ebook")
async def create_ebook_checkout(
    request: CheckoutRequest,
    db: Session = Depends(get_db)
):
    """
    Crea una sesión de checkout para el e-book ($9)
    
    Body:
    {
        "lead_id": 1,
        "price_id": "price_1ABC123..." (opcional)
    }
    
    Returns:
    {
        "url": "https://checkout.stripe.com/c/pay/cs_test_...",
        "session_id": "cs_test_..."
    }
    """
    try:
        result = StripePaymentService.create_checkout_session(
            lead_id=request.lead_id,
            product_type="ebook",
            db=db,
            price_id=request.price_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )
    except Exception as e:
        print(f"❌ Error al crear checkout de e-book: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error al crear sesión de pago: {str(e)}"
        )


@router.post("/create-checkout-session/service")
async def create_service_checkout(
    request: CheckoutRequest,
    db: Session = Depends(get_db)
):
    """
    Crea una sesión de checkout para el servicio completo ($99)
    
    Body:
    {
        "lead_id": 1,
        "price_id": "price_1XYZ789..." (opcional)
    }
    
    Returns:
    {
        "url": "https://checkout.stripe.com/c/pay/cs_test_...",
        "session_id": "cs_test_..."
    }
    """
    try:
        result = StripePaymentService.create_checkout_session(
            lead_id=request.lead_id,
            product_type="service",
            db=db,
            price_id=request.price_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )
    except Exception as e:
        print(f"❌ Error al crear checkout de servicio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error al crear sesión de pago: {str(e)}"
        )


@router.post("/create-checkout-session/subscription")
async def create_subscription_checkout(
    request: CheckoutRequest,
    db: Session = Depends(get_db)
):
    """
    Crea una sesión de checkout para la suscripción premium ($29/mes)
    
    Body:
    {
        "lead_id": 1,
        "price_id": "price_1ABC123..." (opcional)
    }
    
    Returns:
    {
        "url": "https://checkout.stripe.com/c/pay/cs_test_...",
        "session_id": "cs_test_..."
    }
    
    🎯 PLAN PREMIUM ($29/mes):
    - Reporte mensual de Heatmap (Tú vs. Competidores)
    - Alertas automáticas de cambios
    - Soporte prioritario
    - Acceso a dashboard premium
    """
    try:
        result = StripePaymentService.create_checkout_session(
            lead_id=request.lead_id,
            product_type="subscription",
            db=db,
            price_id=request.price_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )
    except Exception as e:
        print(f"❌ Error al crear checkout de suscripción: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Error al crear sesión de pago: {str(e)}"
        )


# Webhook de Stripe
@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint para recibir webhooks de Stripe
    
    🔧 CONFIGURACIÓN EN STRIPE DASHBOARD:
    1. Ir a: https://dashboard.stripe.com/webhooks
    2. Click "Add endpoint"
    3. URL: https://tu-dominio.com/api/stripe/webhook
    4. Eventos a escuchar:
       - checkout.session.completed (REQUERIDO)
       - payment_intent.succeeded (opcional)
    5. Copiar el "Signing secret" (whsec_...)
    6. Agregarlo al archivo .env como STRIPE_WEBHOOK_SECRET
    
    📦 EVENTOS MANEJADOS:
    - checkout.session.completed: 
      * Actualiza Lead.customer_status a 'cliente'
      * Actualiza Order.status a 'completed' (pagada)
      * Si es 'service', marca como lista para equipo de trabajo
      * Si es 'ebook', genera link de descarga
    
    🔒 SEGURIDAD:
    - Verifica la firma de Stripe para validar que el webhook es legítimo
    - Rechaza peticiones sin firma válida
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falta el header 'stripe-signature'"
        )
    
    try:
        result = StripePaymentService.handle_webhook_event(payload, sig_header, db)
        return result
    except Exception as e:
        print(f"❌ Error procesando webhook de Stripe: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/orders/lead/{lead_id}")
async def get_lead_orders(lead_id: int, db: Session = Depends(get_db)):
    """
    Obtiene todas las órdenes de un lead
    """
    orders = StripePaymentService.get_lead_orders(lead_id, db)
    return {
        "lead_id": lead_id,
        "orders": [
            {
                "id": order.id,
                "product_type": order.product_type,
                "amount": order.amount,
                "status": order.status,
                "created_at": order.created_at,
                "completed_at": order.completed_at,
                "download_link": order.download_link
            }
            for order in orders
        ]
    }


@router.get("/order/session/{session_id}")
async def get_order_by_session(session_id: str, db: Session = Depends(get_db)):
    """
    Obtiene una orden por su session_id de Stripe
    Útil para la página de éxito después del pago
    """
    order = StripePaymentService.get_order_by_session(session_id, db)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada"
        )
    
    return {
        "id": order.id,
        "lead_id": order.lead_id,
        "product_type": order.product_type,
        "amount": order.amount,
        "status": order.status,
        "download_link": order.download_link,
        "completed_at": order.completed_at
    }
