from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import stripe
import os

app = FastAPI()

# Stripe Connect setup
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
LOKIGI_ACCOUNT_ID = os.getenv('LOKIGI_STRIPE_ACCOUNT_ID')

@app.post('/purchase-addon')
def purchase_addon(request: Request):
    data = request.json()
    addon_price = data.get('price', 10)  # USD
    developer_account = data.get('developer_account')
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(addon_price * 100),
            currency='usd',
            payment_method_types=['card'],
            transfer_data={
                'amount': int(addon_price * 0.8 * 100),
                'destination': developer_account,
            },
            application_fee_amount=int(addon_price * 0.2 * 100),
            on_behalf_of=developer_account,
        )
        return JSONResponse({'client_secret': payment_intent['client_secret']})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=400)

# Plugin Architecture: Hooks/Slots
@app.get('/dashboard-hooks')
def dashboard_hooks():
    # Ejemplo: lista de widgets/iframes permitidos
    return [
        {'name': 'Menú Digital', 'iframe_url': 'https://widget.menudigital.com', 'sandbox': True},
        {'name': 'POS Integrator', 'iframe_url': 'https://widget.posintegrator.com', 'sandbox': True},
    ]

# App Manifest estándar
# lokigi-manifest.json ejemplo:
# {
#   "name": "Menú Digital Generator",
#   "author": "Juan Perez",
#   "widget_url": "https://widget.menudigital.com",
#   "permissions": [],
#   "languages": ["es", "en"],
#   "screenshots": ["https://..."],
#   "price": 10
# }

# Sandboxing: Solo iframes con sandbox, sin acceso a tokens ni datos sensibles
# (La lógica de frontend debe usar <iframe sandbox="allow-scripts allow-same-origin">)

import requests

# Supabase: Obtener apps y suscripciones
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

@app.get('/api/user-subscriptions')
def user_subscriptions(user_id: str):
    # Consulta Supabase para obtener add-ons activos
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }
    url = f"{SUPABASE_URL}/rest/v1/subscriptions?user_id=eq.{user_id}"
    resp = requests.get(url, headers=headers)
    return resp.json()

@app.get('/api/apps')
def get_apps():
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
    }
    url = f"{SUPABASE_URL}/rest/v1/apps"
    resp = requests.get(url, headers=headers)
    return resp.json()
