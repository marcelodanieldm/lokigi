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
from task_generator import generate_tasks_from_audit

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
        "currency": "usd",
        "type": "one_time"
    },
    "service": {
        "name": "Optimización SEO Local Completa",
        "description": "Servicio completo de optimización + 3 meses de seguimiento",
        "price": 9900,  # $99 en centavos
        "currency": "usd",
        "type": "one_time"
    },
    "subscription": {
        "name": "Plan Premium - Heatmap Mensual",
        "description": "Reporte mensual de competidores + alertas de cambios + soporte prioritario",
        "price": 2900,  # $29 en centavos
        "currency": "usd",
        "type": "subscription",
        "recurring_interval": "month"
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
                # Configurar line_items según el tipo de producto
                if product['type'] == 'subscription':
                    line_items = [{
                        'price_data': {
                            'currency': product['currency'],
                            'product_data': {
                                'name': product['name'],
                                'description': product['description'],
                            },
                            'unit_amount': product['price'],
                            'recurring': {
                                'interval': product['recurring_interval']
                            }
                        },
                        'quantity': 1,
                    }]
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
            
            # Mode depende del tipo de producto
            mode = 'subscription' if product.get('type') == 'subscription' else 'payment'
            
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=line_items,
                mode=mode,
                success_url=f"{FRONTEND_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{FRONTEND_URL}/audit-results?lead_id={lead_id}&canceled=true",
                metadata={
                    "lead_id": str(lead_id),
                    "product_type": product_type,
                    "business_name": lead.nombre_negocio
                }
            )
            
            # Crear orden en estado pending (solo para one-time payments)
            # Para suscripciones, la orden se crea en el webhook
            if product.get('type') != 'subscription':
                product_type_enum = ProductType.EBOOK if product_type == "ebook" else ProductType.SERVICE
                order = Order(
                    lead_id=lead_id,
                    product_type=product_type_enum,
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
        
        elif event_type == 'customer.subscription.created':
            subscription = event['data']['object']
            return StripePaymentService._handle_subscription_created(subscription, db)
        
        elif event_type == 'customer.subscription.updated':
            subscription = event['data']['object']
            return StripePaymentService._handle_subscription_updated(subscription, db)
        
        elif event_type == 'customer.subscription.deleted':
            subscription = event['data']['object']
            return StripePaymentService._handle_subscription_deleted(subscription, db)
        
        elif event_type == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            return StripePaymentService._handle_payment_succeeded(payment_intent, db)
        
        # Evento no manejado (no es un error)
        return {"status": "ignored", "event_type": event_type}
    
    
    @staticmethod
    def _handle_checkout_completed(session: Dict, db: Session) -> Dict:
        """
        Procesa un checkout completado
        
        Maneja 3 casos según el equipo de Data:
        1. $9 (ebook): Dispara email con enlace de descarga
        2. $99 (service): Crea orden de trabajo para Workers
        3. $29/mes (subscription): Activa flag premium_subscriber
        """
        lead_id = int(session['metadata']['lead_id'])
        product_type = session['metadata']['product_type']
        
        # Obtener lead
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"status": "error", "message": "Lead no encontrado"}
        
        # Actualizar lead a CLIENTE (porque pagó)
        lead.customer_status = CustomerStatus.CLIENTE
        if not lead.paid_at:
            lead.paid_at = datetime.utcnow()
        lead.stripe_payment_intent_id = session.get('payment_intent')
        
        # CASO 1: E-BOOK ($9) - Enviar email con descarga
        if product_type == "ebook":
            order = db.query(Order).filter(
                Order.stripe_session_id == session['id']
            ).first()
            
            if order:
                order.stripe_payment_intent_id = session.get('payment_intent')
                order.status = OrderStatus.COMPLETED
                order.completed_at = datetime.utcnow()
                
                # Generar link de descarga
                download_link = StripePaymentService._generate_ebook_download_link(lead, order)
                order.download_link = download_link
                
                print(f"✅ [$9 E-BOOK] Generado para {lead.email}: {download_link}")
                
                # TODO: Enviar email automático con SendGrid/Mailgun (capa gratuita)
                # send_ebook_email(lead.email, lead.nombre, download_link)
                
                result_message = f"E-book generado y enviado a {lead.email}"
            else:
                result_message = "E-book procesado (orden no encontrada)"
        
        # CASO 2: SERVICIO ($99) - Crear orden de trabajo para Workers
        elif product_type == "service":
            order = db.query(Order).filter(
                Order.stripe_session_id == session['id']
            ).first()
            
            if order:
                order.stripe_payment_intent_id = session.get('payment_intent')
                order.status = OrderStatus.COMPLETED  # PAGADA y lista para trabajar
                order.completed_at = datetime.utcnow()
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
2. Agendar reunión inicial
3. Reclamar Google Business Profile
4. Subir fotos con geoetiquetado
5. Optimizar categorías y descripción
6. Implementar estrategia de reseñas
7. Seguimiento mensual (3 meses)

💰 Monto pagado: ${order.amount} USD
📅 Fecha de pago: {order.completed_at.strftime('%Y-%m-%d %H:%M')}
"""
                
                print(f"🎯 [$99 SERVICE] Nueva orden: Order #{order.id} - {lead.nombre_negocio}")
                
                # 🚀 GENERAR TAREAS AUTOMÁTICAMENTE para Workers
                try:
                    tasks_created = generate_tasks_from_audit(
                        order_id=order.id,
                        audit_data=lead.audit_data or {},
                        fallos_criticos=lead.fallos_criticos or [],
                        db=db
                    )
                    print(f"✅ {len(tasks_created)} tareas generadas para Workers")
                except Exception as e:
                    print(f"⚠️  Error generando tareas: {str(e)}")
                
                result_message = f"Orden #{order.id} lista para Workers"
            else:
                result_message = "Servicio procesado (orden no encontrada)"
        
        # CASO 3: SUSCRIPCIÓN ($29/mes) - Activar premium_subscriber
        elif product_type == "subscription":
            subscription_id = session.get('subscription')
            
            # Activar flag de suscriptor premium
            lead.premium_subscriber = True
            lead.subscription_id = subscription_id
            lead.subscription_status = 'active'
            
            # Obtener detalles de la suscripción desde Stripe
            if subscription_id:
                try:
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    lead.subscription_current_period_end = datetime.fromtimestamp(
                        subscription.current_period_end
                    )
                except Exception as e:
                    print(f"⚠️  Error obteniendo detalles de suscripción: {str(e)}")
            
            print(f"✅ [$29/MES SUBSCRIPTION] Activada para {lead.email}")
            print(f"   Subscription ID: {subscription_id}")
            print(f"   Premium features habilitados")
            
            # TODO: Enviar email de bienvenida premium
            # send_premium_welcome_email(lead.email, lead.nombre)
            
            result_message = f"Suscripción premium activada para {lead.email}"
        
        else:
            result_message = f"Producto desconocido: {product_type}"
        
        db.commit()
        
        return {
            "status": "success",
            "lead_id": lead_id,
            "product_type": product_type,
            "message": result_message
        }
    
    
    @staticmethod
    def _handle_subscription_created(subscription: Dict, db: Session) -> Dict:
        """
        Maneja creación de nueva suscripción
        """
        customer_id = subscription.get('customer')
        subscription_id = subscription.get('id')
        
        # Buscar lead por stripe_customer_id
        lead = db.query(Lead).filter(Lead.stripe_customer_id == customer_id).first()
        if not lead:
            return {"status": "error", "message": "Lead no encontrado"}
        
        # Activar premium
        lead.premium_subscriber = True
        lead.subscription_id = subscription_id
        lead.subscription_status = subscription.get('status', 'active')
        lead.subscription_current_period_end = datetime.fromtimestamp(
            subscription.get('current_period_end', 0)
        )
        
        db.commit()
        
        print(f"✅ Suscripción creada: {subscription_id} para {lead.email}")
        
        return {"status": "success", "subscription_id": subscription_id}
    
    
    @staticmethod
    def _handle_subscription_updated(subscription: Dict, db: Session) -> Dict:
        """
        Maneja actualización de suscripción (renovación, cambio de plan, etc.)
        """
        subscription_id = subscription.get('id')
        
        lead = db.query(Lead).filter(Lead.subscription_id == subscription_id).first()
        if not lead:
            return {"status": "error", "message": "Lead no encontrado"}
        
        # Actualizar estado
        new_status = subscription.get('status')
        lead.subscription_status = new_status
        lead.subscription_current_period_end = datetime.fromtimestamp(
            subscription.get('current_period_end', 0)
        )
        
        # Si la suscripción fue cancelada o está past_due, desactivar premium
        if new_status in ['canceled', 'unpaid', 'past_due']:
            lead.premium_subscriber = False
            print(f"⚠️  Suscripción {subscription_id} desactivada: {new_status}")
        else:
            lead.premium_subscriber = True
            print(f"✅ Suscripción {subscription_id} actualizada: {new_status}")
        
        db.commit()
        
        return {"status": "success", "subscription_id": subscription_id, "new_status": new_status}
    
    
    @staticmethod
    def _handle_subscription_deleted(subscription: Dict, db: Session) -> Dict:
        """
        Maneja cancelación de suscripción
        """
        subscription_id = subscription.get('id')
        
        lead = db.query(Lead).filter(Lead.subscription_id == subscription_id).first()
        if not lead:
            return {"status": "error", "message": "Lead no encontrado"}
        
        # Desactivar premium
        lead.premium_subscriber = False
        lead.subscription_status = 'canceled'
        
        db.commit()
        
        print(f"❌ Suscripción cancelada: {subscription_id} para {lead.email}")
        
        # TODO: Enviar email de cancelación
        # send_cancellation_email(lead.email, lead.nombre)
        
        return {"status": "success", "subscription_id": subscription_id}
    
    
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
