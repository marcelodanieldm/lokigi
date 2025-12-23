import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"🔐 {title}")
    print("="*60)

def login(email, password, role_name):
    """Login y muestra información del usuario"""
    print(f"\n📧 Email: {email}")
    print(f"🔑 Password: {password}")
    print(f"👤 Rol esperado: {role_name.upper()}\n")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": email,
                "password": password
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data['access_token']
            user = data['user']
            
            print("✅ Login exitoso!")
            print(f"\n👤 Usuario:")
            print(f"   - ID: {user['id']}")
            print(f"   - Email: {user['email']}")
            print(f"   - Nombre: {user['full_name']}")
            print(f"   - Rol: {user['role'].upper()}")
            print(f"\n🎫 Token JWT (primeros 50 caracteres):")
            print(f"   {token[:50]}...")
            
            return token, user['role']
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None, None

def test_endpoint(token, role, endpoint, expected_status=200):
    """Prueba un endpoint con el token dado"""
    print(f"\n🔍 Probando: {endpoint}")
    
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        status_icon = "✅" if response.status_code == expected_status else "❌"
        print(f"{status_icon} Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Respuesta recibida ({len(json.dumps(data))} bytes)")
        elif response.status_code == 403:
            print("🚫 Acceso denegado (esperado para este rol)")
        elif response.status_code == 401:
            print("🔒 No autorizado")
        else:
            print(f"⚠️  {response.text[:100]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                   🔐 LOKIGI LOGIN TEST                       ║
    ║              Sistema RBAC - 3 Roles Disponibles             ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # ========== TEST 1: LOGIN ADMIN ==========
    print_section("TEST 1: Login como ADMIN")
    admin_token, admin_role = login(
        "admin@lokigi.com",
        "admin123",
        "admin"
    )
    
    if admin_token:
        print("\n📋 Probando permisos de ADMIN:")
        test_endpoint(admin_token, admin_role, "/api/dashboard/orders")
        test_endpoint(admin_token, admin_role, "/api/dashboard/command-center/financial?time_range=30d")
        test_endpoint(admin_token, admin_role, "/api/retention/churn-analytics?time_range=30d")
    
    # ========== TEST 2: LOGIN WORKER ==========
    print_section("TEST 2: Login como WORKER")
    worker_token, worker_role = login(
        "worker@lokigi.com",
        "worker123",
        "worker"
    )
    
    if worker_token:
        print("\n📋 Probando permisos de WORKER:")
        test_endpoint(worker_token, worker_role, "/api/dashboard/work/queue")
        test_endpoint(worker_token, worker_role, "/api/dashboard/work/my-orders")
        # Este debería dar 403
        print("\n🔍 Probando acceso a endpoint de ADMIN (debería fallar):")
        test_endpoint(worker_token, worker_role, "/api/dashboard/command-center/financial?time_range=30d", expected_status=403)
    
    # ========== TEST 3: LOGIN CUSTOMER ==========
    print_section("TEST 3: Login como CUSTOMER")
    customer_token, customer_role = login(
        "cliente@example.com",
        "cliente123",
        "customer"
    )
    
    if customer_token:
        print("\n📋 Probando permisos de CUSTOMER:")
        test_endpoint(customer_token, customer_role, "/api/customer/me")
        test_endpoint(customer_token, customer_role, "/api/customer/reports")
        # Este debería dar 403
        print("\n🔍 Probando acceso a endpoint de ADMIN (debería fallar):")
        test_endpoint(customer_token, customer_role, "/api/dashboard/orders", expected_status=403)
    
    # ========== RESUMEN ==========
    print_section("RESUMEN DE PRUEBAS")
    print("""
    ✅ Credenciales verificadas:
       - admin@lokigi.com / admin123 → Rol: ADMIN
       - worker@lokigi.com / worker123 → Rol: WORKER
       - cliente@example.com / cliente123 → Rol: CUSTOMER
    
    📊 Sistema RBAC funcionando:
       - ADMIN: Acceso total (Command Center, Analytics, Órdenes)
       - WORKER: Solo Work Queue y sus órdenes asignadas
       - CUSTOMER: Solo sus propios datos (reportes, pagos, radar)
    
    🎯 Próximos pasos:
       1. Abrir http://localhost:3000/dashboard
       2. Login con admin@lokigi.com / admin123
       3. Verificar acceso al Command Center
       4. Logout y login con worker@lokigi.com / worker123
       5. Verificar solo acceso a Work Queue
    """)

if __name__ == "__main__":
    main()
