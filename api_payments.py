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
    """
    try:
        result = StripePaymentService.create_checkout_session(
            lead_id=request.lead_id,
            product_type="ebook",
            db=db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/create-checkout-session/service")
async def create_service_checkout(
    request: CheckoutRequest,
    db: Session = Depends(get_db)
):
    """
    Crea una sesión de checkout para el servicio completo ($99)
    """
    try:
        result = StripePaymentService.create_checkout_session(
            lead_id=request.lead_id,
            product_type="service",
            db=db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Webhook de Stripe
@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Endpoint para recibir webhooks de Stripe
    
    Configurar en Stripe Dashboard:
    1. Ir a Developers > Webhooks
    2. Agregar endpoint: https://tu-dominio.com/api/stripe/webhook
    3. Seleccionar eventos: checkout.session.completed, payment_intent.succeeded
    4. Copiar el webhook secret a .env como STRIPE_WEBHOOK_SECRET
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falta el header de firma"
        )
    
    try:
        result = StripePaymentService.handle_webhook_event(payload, sig_header, db)
        return result
    except Exception as e:
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
