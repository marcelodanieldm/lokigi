"""
Servicio de Stripe para pagos y webhooks
Maneja checkout sessions para e-book ($9) y servicio completo ($99)
"""
import stripe
import os
from typing import Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models import Lead, Order, CustomerStatus, ProductType, OrderStatus

# Configuración de Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")

# URLs de redirección
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Precios de productos
PRODUCTS = {
    "ebook": {
        "name": "Plan de Acción SEO Local PDF",
        "description": "Plan personalizado paso a paso para optimizar tu presencia local",
        "price": 900,  # $9 en centavos
        "currency": "usd"
    },
    "service": {
        "name": "Optimización SEO Local Completa",
        "description": "Servicio completo de optimización + 3 meses de seguimiento",
        "price": 9900,  # $99 en centavos
        "currency": "usd"
    }
}


class StripePaymentService:
    """Servicio para manejar pagos con Stripe"""
    
    @staticmethod
    def create_checkout_session(
        lead_id: int,
        product_type: str,
        db: Session
    ) -> Dict:
        """
        Crea una sesión de checkout de Stripe
        
        Args:
            lead_id: ID del lead que realiza la compra
            product_type: 'ebook' o 'service'
            db: Sesión de base de datos
            
        Returns:
            Dict con url de checkout y session_id
        """
        # Verificar que el producto existe
        if product_type not in PRODUCTS:
            raise ValueError(f"Producto '{product_type}' no válido. Usa 'ebook' o 'service'")
        
        # Obtener el lead
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} no encontrado")
        
        product = PRODUCTS[product_type]
        
        try:
            # Crear o recuperar customer de Stripe
            if lead.stripe_customer_id:
                customer_id = lead.stripe_customer_id
            else:
                customer = stripe.Customer.create(
                    email=lead.email,
                    name=lead.nombre,
                    phone=lead.whatsapp or lead.telefono,
                    metadata={
                        "lead_id": lead_id,
                        "business_name": lead.nombre_negocio
                    }
                )
                customer_id = customer.id
                lead.stripe_customer_id = customer_id
                db.commit()
            
            # Crear sesión de checkout
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': product['currency'],
                        'product_data': {
                            'name': product['name'],
                            'description': product['description'],
                        },
                        'unit_amount': product['price'],
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{FRONTEND_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{FRONTEND_URL}/audit-results?lead_id={lead_id}&canceled=true",
                metadata={
                    "lead_id": lead_id,
                    "product_type": product_type,
                    "business_name": lead.nombre_negocio
                }
            )
            
            # Crear orden en estado pending
            order = Order(
                lead_id=lead_id,
                product_type=ProductType.EBOOK if product_type == "ebook" else ProductType.SERVICE,
                amount=product['price'] / 100,  # Convertir centavos a dólares
                currency=product['currency'],
                stripe_session_id=session.id,
                status=OrderStatus.PENDING
            )
            db.add(order)
            
            # Actualizar lead con session ID
            lead.stripe_checkout_session_id = session.id
            db.commit()
            
            return {
                "url": session.url,
                "session_id": session.id
            }
            
        except stripe.error.StripeError as e:
            raise Exception(f"Error de Stripe: {str(e)}")
    
    
    @staticmethod
    def handle_webhook_event(payload: bytes, sig_header: str, db: Session) -> Dict:
        """
        Maneja eventos de webhook de Stripe
        
        Args:
            payload: Cuerpo de la petición
            sig_header: Header de firma de Stripe
            db: Sesión de base de datos
            
        Returns:
            Dict con el resultado del procesamiento
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise Exception("Payload inválido")
        except stripe.error.SignatureVerificationError:
            raise Exception("Firma inválida")
        
        # Manejar el evento
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            return StripePaymentService._handle_checkout_completed(session, db)
        
        elif event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            return StripePaymentService._handle_payment_succeeded(payment_intent, db)
        
        return {"status": "ignored", "event_type": event['type']}
    
    
    @staticmethod
    def _handle_checkout_completed(session: Dict, db: Session) -> Dict:
        """
        Procesa un checkout completado
        """
        lead_id = int(session['metadata']['lead_id'])
        product_type = session['metadata']['product_type']
        
        # Obtener lead y orden
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        order = db.query(Order).filter(
            Order.stripe_session_id == session['id']
        ).first()
        
        if not lead or not order:
            return {"status": "error", "message": "Lead u orden no encontrados"}
        
        # Actualizar lead a CLIENTE
        lead.customer_status = CustomerStatus.CLIENTE
        lead.paid_at = datetime.utcnow()
        lead.stripe_payment_intent_id = session.get('payment_intent')
        
        # Actualizar orden
        order.stripe_payment_intent_id = session.get('payment_intent')
        order.status = OrderStatus.COMPLETED
        order.completed_at = datetime.utcnow()
        
        # Procesamiento específico por producto
        if product_type == "ebook":
            # Generar link de descarga del e-book
            download_link = StripePaymentService._generate_ebook_download_link(lead, order)
            order.download_link = download_link
            
            # TODO: Enviar email con link de descarga
            # send_email(lead.email, download_link)
            
            result_message = "E-book enviado por email"
            
        elif product_type == "service":
            # Crear nota para el equipo de trabajo
            order.notes = f"""
            NUEVO CLIENTE - SERVICIO COMPLETO
            Negocio: {lead.nombre_negocio}
            Cliente: {lead.nombre}
            Email: {lead.email}
            WhatsApp: {lead.whatsapp or lead.telefono}
            Score inicial: {lead.score_visibilidad}/100
            
            ACCIÓN REQUERIDA:
            1. Contactar al cliente en 24h
            2. Agendar reunión inicial
            3. Comenzar optimización de Google Business Profile
            4. Crear landing page
            """
            
            # TODO: Notificar al equipo (Slack, email, etc.)
            # notify_team(order)
            
            result_message = "Orden creada para el equipo"
        
        db.commit()
        
        return {
            "status": "success",
            "lead_id": lead_id,
            "product_type": product_type,
            "message": result_message
        }
    
    
    @staticmethod
    def _handle_payment_succeeded(payment_intent: Dict, db: Session) -> Dict:
        """
        Procesa un pago exitoso
        """
        # Actualizar registro con payment_intent_id si es necesario
        return {"status": "success", "event": "payment_intent.succeeded"}
    
    
    @staticmethod
    def _generate_ebook_download_link(lead: Lead, order: Order) -> str:
        """
        Genera un link de descarga único para el e-book
        
        En producción, esto debería:
        1. Generar PDF personalizado con los datos del lead
        2. Subirlo a S3/Cloud Storage
        3. Generar URL firmada con expiración
        
        Por ahora retorna un placeholder
        """
        # TODO: Implementar generación real de PDF
        return f"https://lokigi.com/downloads/{order.id}/ebook-seo-local.pdf"
    
    
    @staticmethod
    def get_order_by_session(session_id: str, db: Session) -> Optional[Order]:
        """
        Obtiene una orden por su session_id de Stripe
        """
        return db.query(Order).filter(
            Order.stripe_session_id == session_id
        ).first()
    
    
    @staticmethod
    def get_lead_orders(lead_id: int, db: Session):
        """
        Obtiene todas las órdenes de un lead
        """
        return db.query(Order).filter(
            Order.lead_id == lead_id
        ).order_by(Order.created_at.desc()).all()
