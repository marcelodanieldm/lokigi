# Guía de Configuración de Stripe para Lokigi

## 🚀 Setup Rápido

### 1. Crear Cuenta en Stripe
1. Ve a [stripe.com](https://stripe.com) y crea una cuenta
2. Activa el modo de prueba (Test Mode) en el dashboard

### 2. Obtener API Keys

#### En Stripe Dashboard:
1. Ve a **Developers** > **API keys**
2. Copia las siguientes keys:
   - **Publishable key** (empieza con `pk_test_`)
   - **Secret key** (empieza con `sk_test_`) ⚠️ NO compartir

#### En tu archivo `.env`:
```bash
STRIPE_SECRET_KEY=sk_test_tu_clave_aqui
STRIPE_PUBLISHABLE_KEY=pk_test_tu_clave_aqui
```

### 3. Configurar Webhook

Los webhooks son necesarios para procesar pagos automáticamente.

#### Desarrollo Local (con Stripe CLI):
```bash
# Instalar Stripe CLI
# Windows: scoop install stripe
# Mac: brew install stripe/stripe-cli/stripe
# Linux: https://stripe.com/docs/stripe-cli

# Login
stripe login

# Forward webhooks a tu backend local
stripe listen --forward-to localhost:8000/api/stripe/webhook

# Copiar el webhook secret que aparece (empieza con whsec_)
```

Agregar a `.env`:
```bash
STRIPE_WEBHOOK_SECRET=whsec_el_secret_que_copiaste
```

#### Producción (con URL pública):
1. Ve a **Developers** > **Webhooks**
2. Click **Add endpoint**
3. URL: `https://tu-dominio.com/api/stripe/webhook`
4. Seleccionar eventos:
   - `checkout.session.completed`
   - `payment_intent.succeeded`
5. Copiar el **Signing secret**

### 4. Probar la Integración

#### Tarjetas de prueba de Stripe:
- **Éxito**: `4242 4242 4242 4242`
- **Requiere autenticación**: `4000 0027 6000 3184`
- **Declinada**: `4000 0000 0000 0002`

**Datos adicionales** (cualquier valor funciona en test mode):
- Fecha: Cualquier fecha futura (ej: 12/25)
- CVC: Cualquier 3 dígitos (ej: 123)
- ZIP: Cualquier código postal

### 5. Verificar Funcionamiento

1. Iniciar backend:
```bash
cd backend
python main.py  # o uvicorn main:app --reload
```

2. Iniciar frontend:
```bash
cd frontend
npm run dev
```

3. En el navegador:
   - Abrir `http://localhost:3000/audit-results`
   - Completar formulario de lead
   - Click en "Comprar por $9" o "Contratar por $99"
   - Usar tarjeta de prueba `4242 4242 4242 4242`
   - Verificar que se completa el pago

4. Verificar en Stripe Dashboard:
   - Ve a **Payments**
   - Deberías ver el pago listado
   - En **Customers** deberías ver el cliente creado
   - En **Webhooks** > **Events** verás los eventos procesados

### 6. Ver Webhooks Procesados

En la consola donde corre `stripe listen`:
```
<- checkout.session.completed [evt_1xxxxxx]
-> POST /api/stripe/webhook [200]
```

En la consola del backend:
```
INFO: Lead 1 actualizado a CLIENTE
INFO: Orden 1 completada - ebook
```

### 7. Base de Datos

Verificar que se guardó correctamente:
```bash
# En Python
python
>>> from database import SessionLocal
>>> from models import Lead, Order
>>> db = SessionLocal()
>>> leads = db.query(Lead).all()
>>> for lead in leads:
...     print(f"{lead.email} - {lead.customer_status}")
>>> orders = db.query(Order).all()
>>> for order in orders:
...     print(f"Order {order.id} - {order.product_type} - {order.status}")
```

## 🔒 Seguridad

### ⚠️ NUNCA subir a Git:
- `.env` (debe estar en `.gitignore`)
- Claves de producción (`sk_live_*`)
- Webhook secrets

### ✅ Sí subir a Git:
- `.env.example` (plantilla sin valores reales)
- Código de integración

### Modo Producción:
Cuando estés listo para cobros reales:
1. Desactiva **Test mode** en Stripe Dashboard
2. Obtén nuevas keys de producción
3. Actualiza `.env` con keys de producción
4. Configura webhooks de producción con URL real
5. ¡NUNCA compartas las keys de producción!

## 📊 Productos Configurados

### E-book ($9)
- Producto: "Plan de Acción SEO Local PDF"
- Precio: $9 USD
- Entregable: Link de descarga automático

### Servicio ($99)
- Producto: "Optimización SEO Local Completa"
- Precio: $99 USD
- Entregable: Orden para equipo de trabajo

## 🐛 Troubleshooting

### Error: "No signature found"
- Verificar que `STRIPE_WEBHOOK_SECRET` esté configurado
- Verificar que `stripe listen` esté corriendo

### Error: "Invalid API Key"
- Verificar que la key empiece con `sk_test_` o `sk_live_`
- Verificar que no tenga espacios al inicio/final

### Webhook no llega al backend
- Verificar que el backend esté corriendo en el puerto correcto
- Verificar que la URL en `stripe listen` coincida
- Ver logs de Stripe CLI para errores

### Pago completado pero no se actualiza la BD
- Ver logs del webhook endpoint
- Verificar que los eventos estén configurados en Stripe Dashboard
- Verificar que el webhook secret sea correcto

## 📚 Recursos

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Testing](https://stripe.com/docs/testing)
- [Stripe CLI](https://stripe.com/docs/stripe-cli)
- [Webhooks Guide](https://stripe.com/docs/webhooks)
