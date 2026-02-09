"""
Script de prueba para verificar la integración de pagos
Ejecutar con: python test_payments.py
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_create_lead():
    """Test 1: Crear un nuevo lead"""
    print("\n" + "="*60)
    print("TEST 1: Crear un nuevo lead")
    print("="*60)
    
    lead_data = {
        "nombre": "Juan Pérez",
        "email": "juan.perez@test.com",
        "telefono": "+1234567890",
        "whatsapp": "+1234567890",
        "nombre_negocio": "Restaurante El Buen Sabor",
        "score_visibilidad": 45,
        "fallos_criticos": {
            "sin_perfil": False,
            "sin_fotos": True,
            "sin_resenas": True
        }
    }
    
    response = requests.post(f"{BASE_URL}/leads", json=lead_data)
    
    if response.status_code == 201:
        lead = response.json()
        print(f"✅ Lead creado exitosamente")
        print(f"   ID: {lead['id']}")
        print(f"   Email: {lead['email']}")
        print(f"   Negocio: {lead['nombre_negocio']}")
        print(f"   Score: {lead['score_visibilidad']}/100")
        return lead['id']
    else:
        print(f"❌ Error al crear lead: {response.status_code}")
        print(f"   {response.json()}")
        return None


def test_create_checkout_ebook(lead_id):
    """Test 2: Crear checkout session para e-book"""
    print("\n" + "="*60)
    print("TEST 2: Crear sesión de checkout para E-book ($9)")
    print("="*60)
    
    checkout_data = {
        "lead_id": lead_id
    }
    
    response = requests.post(
        f"{BASE_URL}/create-checkout-session/ebook",
        json=checkout_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Sesión de checkout creada")
        print(f"   URL: {result['url']}")
        print(f"   Session ID: {result['session_id']}")
        print(f"\n   👉 Abre esta URL en el navegador para completar el pago:")
        print(f"   {result['url']}")
        return result['session_id']
    else:
        print(f"❌ Error al crear checkout: {response.status_code}")
        print(f"   {response.json()}")
        return None


def test_create_checkout_service(lead_id):
    """Test 3: Crear checkout session para servicio"""
    print("\n" + "="*60)
    print("TEST 3: Crear sesión de checkout para Servicio ($99)")
    print("="*60)
    
    checkout_data = {
        "lead_id": lead_id
    }
    
    response = requests.post(
        f"{BASE_URL}/create-checkout-session/service",
        json=checkout_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Sesión de checkout creada")
        print(f"   URL: {result['url']}")
        print(f"   Session ID: {result['session_id']}")
        print(f"\n   👉 Abre esta URL en el navegador para completar el pago:")
        print(f"   {result['url']}")
        return result['session_id']
    else:
        print(f"❌ Error al crear checkout: {response.status_code}")
        print(f"   {response.json()}")
        return None


def test_get_lead_orders(lead_id):
    """Test 4: Obtener órdenes de un lead"""
    print("\n" + "="*60)
    print("TEST 4: Obtener órdenes del lead")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/orders/lead/{lead_id}")
    
    if response.status_code == 200:
        data = response.json()
        orders = data['orders']
        print(f"✅ Lead tiene {len(orders)} orden(es)")
        for i, order in enumerate(orders, 1):
            print(f"\n   Orden {i}:")
            print(f"   - ID: {order['id']}")
            print(f"   - Producto: {order['product_type']}")
            print(f"   - Monto: ${order['amount']}")
            print(f"   - Status: {order['status']}")
            print(f"   - Creada: {order['created_at']}")
    else:
        print(f"❌ Error al obtener órdenes: {response.status_code}")


def main():
    print("\n" + "🚀"*30)
    print("LOKIGI - TEST DE INTEGRACIÓN DE PAGOS")
    print("🚀"*30)
    
    print("\n⚠️  REQUISITOS:")
    print("1. Backend corriendo en http://localhost:8000")
    print("2. Variables de entorno configuradas en .env:")
    print("   - STRIPE_SECRET_KEY")
    print("   - STRIPE_WEBHOOK_SECRET")
    print("3. Base de datos inicializada")
    
    input("\nPresiona Enter para comenzar las pruebas...")
    
    # Test 1: Crear lead
    lead_id = test_create_lead()
    if not lead_id:
        print("\n❌ No se pudo crear el lead. Abortando pruebas.")
        return
    
    # Test 2: Crear checkout de e-book
    test_create_checkout_ebook(lead_id)
    
    # Test 3: Crear checkout de servicio
    test_create_checkout_service(lead_id)
    
    # Test 4: Ver órdenes creadas
    test_get_lead_orders(lead_id)
    
    print("\n" + "="*60)
    print("PRUEBAS COMPLETADAS")
    print("="*60)
    print("\n📝 PRÓXIMOS PASOS:")
    print("1. Abre alguna de las URLs de Stripe checkout en el navegador")
    print("2. Usa una tarjeta de prueba de Stripe:")
    print("   - Número: 4242 4242 4242 4242")
    print("   - Fecha: cualquier fecha futura")
    print("   - CVC: cualquier 3 dígitos")
    print("3. Completa el pago")
    print("4. El webhook de Stripe actualizará automáticamente la orden a 'paid'")
    print("\n💡 Para probar el webhook localmente, usa Stripe CLI:")
    print("   stripe listen --forward-to localhost:8000/api/stripe/webhook")
    print()


if __name__ == "__main__":
    main()
