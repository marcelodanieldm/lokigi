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

# Configuración de Stripe desde variables de entorno
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Validar que las variables de entorno estén configuradas
if not stripe.api_key or stripe.api_key.startswith("sk_test_..."):
    print("⚠️  WARNING: STRIPE_SECRET_KEY no configurada correctamente en .env")
if not STRIPE_WEBHOOK_SECRET or STRIPE_WEBHOOK_SECRET.startswith("whsec_..."):
    print("⚠️  WARNING: STRIPE_WEBHOOK_SECRET no configurada correctamente en .env")

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
        db: Session,
        price_id: Optional[str] = None  # Opcional: usar price_id de Stripe en lugar de price_data
    ) -> Dict:
        """
        Crea una sesión de checkout de Stripe
        
        Args:
            lead_id: ID del lead que realiza la compra
            product_type: 'ebook' o 'service'
            db: Sesión de base de datos
            price_id: (Opcional) ID de precio de Stripe (ej: price_1A2B3C4D5E6F)
            
        Returns:
            Dict con url de checkout y session_id
            
        Raises:
            ValueError: Si el producto o lead no existen
            Exception: Si hay un error de red o de Stripe
        """
        # Validar que el producto existe
        if product_type not in PRODUCTS:
            raise ValueError(f"Producto '{product_type}' no válido. Usa 'ebook' o 'service'")
        
        # Obtener el lead
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} no encontrado")
        
        if not lead.email:
            raise ValueError(f"Lead {lead_id} no tiene email configurado")
        
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
            # Si se proporciona price_id, usar ese. Si no, usar price_data
            if price_id:
                line_items = [{'price': price_id, 'quantity': 1}]
            else:
                line_items = [{
                    'price_data': {
                        'currency': product['currency'],
                        'product_data': {
                            'name': product['name'],
                            'description': product['description'],
                        },
                        'unit_amount': product['price'],
                    },
                    'quantity': 1,
                }]
            
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=line_items,
                mode='payment',
                success_url=f"{FRONTEND_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{FRONTEND_URL}/audit-results?lead_id={lead_id}&canceled=true",
                metadata={
                    "lead_id": str(lead_id),
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
            
        except stripe.error.CardError as e:
            # Error con la tarjeta del cliente
            raise Exception(f"Error de tarjeta: {e.user_message}")
        except stripe.error.RateLimitError as e:
            # Demasiadas peticiones a la API de Stripe
            raise Exception("Servicio temporalmente no disponible. Por favor intenta en unos segundos.")
        except stripe.error.InvalidRequestError as e:
            # Parámetros inválidos en la petición
            raise Exception(f"Error de configuración: {str(e)}")
        except stripe.error.AuthenticationError as e:
            # Error de autenticación con Stripe
            raise Exception("Error de autenticación con el servicio de pagos. Contacta a soporte.")
        except stripe.error.APIConnectionError as e:
            # Error de red al comunicarse con Stripe
            raise Exception("Error de conexión con el servicio de pagos. Verifica tu conexión a internet.")
        except stripe.error.StripeError as e:
            # Error genérico de Stripe
            raise Exception(f"Error al procesar el pago: {str(e)}")
        except Exception as e:
            # Error inesperado
            raise Exception(f"Error inesperado al crear sesión de checkout: {str(e)}")
    
    
    @staticmethod
    def handle_webhook_event(payload: bytes, sig_header: str, db: Session) -> Dict:
        """
        Maneja eventos de webhook de Stripe
        
        Eventos soportados:
        - checkout.session.completed: Cuando el pago se completa exitosamente
        - payment_intent.succeeded: Cuando el payment intent se confirma
        
        Args:
            payload: Cuerpo de la petición (raw bytes)
            sig_header: Header 'stripe-signature' de la petición
            db: Sesión de base de datos
            
        Returns:
            Dict con el resultado del procesamiento
            
        Raises:
            Exception: Si la firma es inválida o hay error en el procesamiento
        """
        if not STRIPE_WEBHOOK_SECRET:
            raise Exception("STRIPE_WEBHOOK_SECRET no configurado en variables de entorno")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            raise Exception(f"Payload de webhook inválido: {str(e)}")
        except stripe.error.SignatureVerificationError as e:
            raise Exception(f"Firma de webhook inválida: {str(e)}")
        
        event_type = event.get('type')
        print(f"📩 Webhook recibido: {event_type}")
        
        # Manejar el evento según su tipo
        if event_type == 'checkout.session.completed':
            session = event['data']['object']
            return StripePaymentService._handle_checkout_completed(session, db)
        
        elif event_type == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            return StripePaymentService._handle_payment_succeeded(payment_intent, db)
        
        # Evento no manejado (no es un error)
        return {"status": "ignored", "event_type": event_type}
    
    
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
        
        # Actualizar lead a CLIENTE (es cliente porque pagó)
        lead.customer_status = CustomerStatus.CLIENTE
        if not lead.paid_at:  # Solo actualizar la primera vez
            lead.paid_at = datetime.utcnow()
        lead.stripe_payment_intent_id = session.get('payment_intent')
        
        # Actualizar orden de PENDING a COMPLETED
        # El status va de: pending (creada) -> completed (pagada)
        order.stripe_payment_intent_id = session.get('payment_intent')
        order.status = OrderStatus.COMPLETED  # Marca como 'paid' (completado significa pagado)
        order.completed_at = datetime.utcnow()
        
        # Procesamiento específico por producto
        if product_type == "ebook":
            # Generar link de descarga del e-book
            download_link = StripePaymentService._generate_ebook_download_link(lead, order)
            order.download_link = download_link
            
            print(f"✅ E-book generado para {lead.email}: {download_link}")
            
            # TODO: Enviar email con link de descarga
            # send_ebook_email(lead.email, lead.nombre, download_link)
            
            result_message = f"E-book generado y listo para enviar a {lead.email}"
            
        elif product_type == "service":
            # Marcar orden como lista para el equipo de trabajo
            # El status 'completed' indica que está PAGADA y lista para trabajar
            order.notes = f"""🎯 NUEVA ORDEN DE SERVICIO - PAGADA

📊 INFORMACIÓN DEL CLIENTE:
Negocio: {lead.nombre_negocio}
Cliente: {lead.nombre}
Email: {lead.email}
Teléfono: {lead.telefono}
WhatsApp: {lead.whatsapp or lead.telefono}

📈 AUDITORÍA INICIAL:
Score de visibilidad: {lead.score_visibilidad}/100

✅ PRÓXIMOS PASOS:
1. Contactar al cliente en las próximas 24 horas
2. Agendar reunión inicial para definir estrategia
3. Reclamar y optimizar Google Business Profile
4. Subir fotos con geoetiquetado
5. Configurar mensajes automáticos
6. Crear landing page optimizada
7. Implementar estrategia de reseñas
8. Seguimiento mensual (3 meses)

💰 Monto pagado: ${order.amount} USD
📅 Fecha de pago: {order.completed_at.strftime('%Y-%m-%d %H:%M')}
"""
            
            print(f"🎯 Nueva orden de servicio pagada: Order #{order.id} - {lead.nombre_negocio}")
            print(f"   Cliente: {lead.nombre} ({lead.email})")
            print(f"   Score inicial: {lead.score_visibilidad}/100")
            
            # TODO: Notificar al equipo de trabajo
            # send_team_notification(order)
            # slack_notify(f"Nueva orden pagada: {lead.nombre_negocio} - ${order.amount}")
            
            result_message = f"Orden #{order.id} marcada como PAGADA y lista para el equipo de trabajo"
        
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
