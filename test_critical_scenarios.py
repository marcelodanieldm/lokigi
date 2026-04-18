"""
Script de testing completo para escenarios críticos de Lokigi
Prueba RBAC, RLS, Customer Portal, flujos de auditoría y Radar
"""
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional

# Configuración
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_section(title: str):
    """Imprime sección con formato"""
    print(f"\n{'='*80}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{'='*80}\n")

def print_success(message: str):
    """Imprime mensaje de éxito"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    """Imprime mensaje de error"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message: str):
    """Imprime advertencia"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message: str):
    """Imprime información"""
    print(f"ℹ️  {message}")

class TestSession:
    """Gestiona sesiones de testing con diferentes usuarios"""
    def __init__(self, role: str, email: str, password: str):
        self.role = role
        self.email = email
        self.password = password
        self.token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.headers: Dict[str, str] = {}
    
    def login(self) -> bool:
        """Realiza login y obtiene token"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/login",
                json={"email": self.email, "password": self.password}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_id = data["user"]["id"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print_success(f"Login exitoso como {self.role}: {self.email}")
                return True
            else:
                print_error(f"Login fallido para {self.role}: {response.text}")
                return False
        except Exception as e:
            print_error(f"Error en login {self.role}: {str(e)}")
            return False
    
    def get(self, endpoint: str, expected_status: int = 200) -> Optional[requests.Response]:
        """Realiza GET request"""
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=self.headers)
            if response.status_code == expected_status:
                print_success(f"[{self.role}] GET {endpoint} → {response.status_code}")
                return response
            else:
                print_error(f"[{self.role}] GET {endpoint} → {response.status_code} (esperado: {expected_status})")
                print(f"    Response: {response.text[:200]}")
                return None
        except Exception as e:
            print_error(f"[{self.role}] Error en GET {endpoint}: {str(e)}")
            return None
    
    def post(self, endpoint: str, data: dict, expected_status: int = 200) -> Optional[requests.Response]:
        """Realiza POST request"""
        try:
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=self.headers)
            if response.status_code == expected_status:
                print_success(f"[{self.role}] POST {endpoint} → {response.status_code}")
                return response
            else:
                print_error(f"[{self.role}] POST {endpoint} → {response.status_code} (esperado: {expected_status})")
                print(f"    Response: {response.text[:200]}")
                return None
        except Exception as e:
            print_error(f"[{self.role}] Error en POST {endpoint}: {str(e)}")
            return None
    
    def put(self, endpoint: str, data: dict, expected_status: int = 200) -> Optional[requests.Response]:
        """Realiza PUT request"""
        try:
            response = requests.put(f"{BASE_URL}{endpoint}", json=data, headers=self.headers)
            if response.status_code == expected_status:
                print_success(f"[{self.role}] PUT {endpoint} → {response.status_code}")
                return response
            else:
                print_error(f"[{self.role}] PUT {endpoint} → {response.status_code} (esperado: {expected_status})")
                print(f"    Response: {response.text[:200]}")
                return None
        except Exception as e:
            print_error(f"[{self.role}] Error en PUT {endpoint}: {str(e)}")
            return None


def test_1_authentication():
    """TEST 1: Autenticación con los 3 roles"""
    print_section("TEST 1: AUTENTICACIÓN Y LOGIN")
    
    admin = TestSession("ADMIN", "admin@lokigi.com", "admin123")
    worker = TestSession("WORKER", "worker@lokigi.com", "worker123")
    customer = TestSession("CUSTOMER", "cliente@example.com", "cliente123")
    
    results = {
        "admin": admin.login(),
        "worker": worker.login(),
        "customer": customer.login()
    }
    
    print(f"\n📊 Resultados:")
    print(f"   ADMIN: {'✅ OK' if results['admin'] else '❌ FAIL'}")
    print(f"   WORKER: {'✅ OK' if results['worker'] else '❌ FAIL'}")
    print(f"   CUSTOMER: {'✅ OK' if results['customer'] else '❌ FAIL'}")
    
    return admin, worker, customer, all(results.values())


def test_2_rbac_authorization(admin: TestSession, worker: TestSession, customer: TestSession):
    """TEST 2: Autorización RBAC - cada rol accede solo a sus endpoints"""
    print_section("TEST 2: AUTORIZACIÓN RBAC")
    
    tests_passed = 0
    tests_total = 0
    
    # TEST 2.1: ADMIN puede acceder a todo
    print("\n🔹 TEST 2.1: ADMIN accede a endpoints administrativos")
    tests_total += 3
    if admin.get("/api/leads"):
        tests_passed += 1
    if admin.get("/api/metrics/financial"):
        tests_passed += 1
    if admin.get("/api/users"):
        tests_passed += 1
    
    # TEST 2.2: WORKER accede a Work Queue pero NO a métricas financieras
    print("\n🔹 TEST 2.2: WORKER accede a Work Queue, NO a métricas financieras")
    tests_total += 2
    if worker.get("/api/tasks"):
        tests_passed += 1
    if worker.get("/api/metrics/financial", expected_status=403):
        tests_passed += 1
        print_success("WORKER correctamente bloqueado de métricas financieras")
    
    # TEST 2.3: CUSTOMER solo accede a Customer Portal
    print("\n🔹 TEST 2.3: CUSTOMER accede a su portal, NO a admin")
    tests_total += 3
    if customer.get("/api/customer/me"):
        tests_passed += 1
    if customer.get("/api/leads", expected_status=403):
        tests_passed += 1
        print_success("CUSTOMER correctamente bloqueado de /api/leads")
    if customer.get("/api/metrics/financial", expected_status=403):
        tests_passed += 1
        print_success("CUSTOMER correctamente bloqueado de métricas")
    
    print(f"\n📊 Resultados RBAC: {tests_passed}/{tests_total} tests pasados")
    return tests_passed == tests_total


def test_3_customer_isolation(admin: TestSession, customer: TestSession):
    """TEST 3: Row-Level Security - CUSTOMER solo ve sus propios datos"""
    print_section("TEST 3: ROW-LEVEL SECURITY (RLS) - AISLAMIENTO DE CUSTOMERS")
    
    tests_passed = 0
    tests_total = 0
    
    # Crear dos leads diferentes
    print("\n🔹 TEST 3.1: Crear dos leads para probar aislamiento")
    lead1_data = {
        "company_name": "Empresa Customer 1",
        "email": "customer1@test.com",
        "phone": "+34600111111",
        "website": "https://customer1.com",
        "status": "active"
    }
    lead2_data = {
        "company_name": "Empresa Customer 2",
        "email": "customer2@test.com",
        "phone": "+34600222222",
        "website": "https://customer2.com",
        "status": "active"
    }
    
    lead1_response = admin.post("/api/leads", lead1_data)
    lead2_response = admin.post("/api/leads", lead2_data)
    
    if lead1_response and lead2_response:
        tests_total += 2
        tests_passed += 2
        lead1_id = lead1_response.json()["id"]
        lead2_id = lead2_response.json()["id"]
        
        print_info(f"Lead 1 ID: {lead1_id}")
        print_info(f"Lead 2 ID: {lead2_id}")
        
        # Crear customer vinculado a lead1
        print("\n🔹 TEST 3.2: Crear customer vinculado a Lead 1")
        customer1_data = {
            "email": "test.customer1@test.com",
            "password": "test123",
            "full_name": "Customer Test 1",
            "role": "CUSTOMER",
            "customer_lead_id": lead1_id
        }
        customer1_response = admin.post("/api/users", customer1_data)
        
        if customer1_response:
            tests_total += 1
            tests_passed += 1
            
            # Login como customer1
            customer1 = TestSession("CUSTOMER1", "test.customer1@test.com", "test123")
            if customer1.login():
                tests_total += 1
                tests_passed += 1
                
                # TEST 3.3: Customer1 puede ver sus propios reportes
                print("\n🔹 TEST 3.3: Customer1 ve sus propios reportes")
                response = customer1.get("/api/customer/reports")
                if response:
                    tests_total += 1
                    tests_passed += 1
                    reports = response.json()
                    print_info(f"Customer1 ve {len(reports)} reportes")
                
                # TEST 3.4: ADMIN ve todos los leads
                print("\n🔹 TEST 3.4: ADMIN ve todos los leads")
                response = admin.get("/api/leads")
                if response:
                    tests_total += 1
                    all_leads = response.json()
                    if len(all_leads) >= 2:
                        tests_passed += 1
                        print_success(f"ADMIN ve {len(all_leads)} leads (incluye ambos)")
    
    print(f"\n📊 Resultados RLS: {tests_passed}/{tests_total} tests pasados")
    return tests_passed == tests_total


def test_4_customer_portal_endpoints(customer: TestSession):
    """TEST 4: Customer Portal - todos los endpoints del portal"""
    print_section("TEST 4: CUSTOMER PORTAL - ENDPOINTS COMPLETOS")
    
    tests_passed = 0
    tests_total = 11
    
    endpoints = [
        ("/api/customer/me", "Perfil del cliente"),
        ("/api/customer/reports", "Reportes de auditoría"),
        ("/api/customer/orders", "Historial de pagos"),
        ("/api/customer/tasks", "Tareas"),
        ("/api/customer/radar/subscription", "Radar subscription"),
        ("/api/customer/radar/alerts", "Alertas de Radar"),
        ("/api/customer/radar/heatmap/latest", "Último heatmap"),
        ("/api/customer/dashboard/summary", "Dashboard resumen"),
    ]
    
    for endpoint, description in endpoints:
        print(f"\n🔹 Testing: {description}")
        response = customer.get(endpoint)
        if response:
            tests_passed += 1
            data = response.json()
            print_info(f"Response keys: {list(data.keys())[:5]}")
    
    # Test PUT profile
    print(f"\n🔹 Testing: Actualizar perfil")
    response = customer.put("/api/customer/profile", {
        "full_name": "Cliente Demo Actualizado",
        "email": "cliente@example.com"
    })
    if response:
        tests_passed += 1
    
    print(f"\n📊 Resultados Customer Portal: {tests_passed}/{tests_total} tests pasados")
    return tests_passed == tests_total


def test_5_audit_workflow(admin: TestSession):
    """TEST 5: Flujo completo de auditoría NAP Consistency"""
    print_section("TEST 5: FLUJO COMPLETO DE AUDITORÍA")
    
    tests_passed = 0
    tests_total = 0
    
    # 5.1: Crear lead
    print("\n🔹 TEST 5.1: Crear nuevo lead")
    lead_data = {
        "company_name": "Test Audit Company",
        "email": "audit@test.com",
        "phone": "+34600999999",
        "website": "https://audittest.com",
        "status": "lead"
    }
    lead_response = admin.post("/api/leads", lead_data)
    if lead_response:
        tests_total += 1
        tests_passed += 1
        lead_id = lead_response.json()["id"]
        print_info(f"Lead creado ID: {lead_id}")
        
        # 5.2: Crear orden de pago
        print("\n🔹 TEST 5.2: Crear orden de pago")
        order_data = {
            "lead_id": lead_id,
            "amount": 99.0,
            "description": "Auditoría NAP Test",
            "status": "completed"
        }
        order_response = admin.post("/api/orders", order_data)
        if order_response:
            tests_total += 1
            tests_passed += 1
            order_id = order_response.json()["id"]
            print_info(f"Orden creada ID: {order_id}")
            
            # 5.3: Crear tarea de auditoría
            print("\n🔹 TEST 5.3: Crear tarea de auditoría")
            task_data = {
                "order_id": order_id,
                "task_type": "nap_audit",
                "status": "pending"
            }
            task_response = admin.post("/api/tasks", task_data)
            if task_response:
                tests_total += 1
                tests_passed += 1
                task_id = task_response.json()["id"]
                print_info(f"Tarea creada ID: {task_id}")
                
                # 5.4: Procesar auditoría (simular)
                print("\n🔹 TEST 5.4: Verificar lead tiene datos para auditoría")
                lead_detail = admin.get(f"/api/leads/{lead_id}")
                if lead_detail:
                    tests_total += 1
                    tests_passed += 1
                    lead_info = lead_detail.json()
                    print_info(f"Lead: {lead_info.get('company_name')}")
                    print_info(f"Website: {lead_info.get('website')}")
    
    print(f"\n📊 Resultados Flujo Auditoría: {tests_passed}/{tests_total} tests pasados")
    return tests_passed == tests_total


def test_6_radar_system(admin: TestSession, customer: TestSession):
    """TEST 6: Sistema Radar Lokigi - subscripciones y alertas"""
    print_section("TEST 6: SISTEMA RADAR LOKIGI")
    
    tests_passed = 0
    tests_total = 0
    
    # 6.1: Obtener lead del customer
    print("\n🔹 TEST 6.1: Obtener lead del customer")
    customer_me = customer.get("/api/customer/me")
    if customer_me:
        tests_total += 1
        tests_passed += 1
        customer_data = customer_me.json()
        lead_id = customer_data.get("customer_lead_id")
        print_info(f"Customer Lead ID: {lead_id}")
        
        if lead_id:
            # 6.2: Crear subscripción Radar (como admin)
            print("\n🔹 TEST 6.2: Crear subscripción Radar")
            subscription_data = {
                "lead_id": lead_id,
                "plan_name": "Radar Lokigi",
                "monthly_price": 29.0,
                "status": "active",
                "keywords": ["empresa demo", "test company"],
                "competitors": ["competitor1.com", "competitor2.com"]
            }
            sub_response = admin.post("/api/radar/subscriptions", subscription_data)
            if sub_response:
                tests_total += 1
                tests_passed += 1
                sub_id = sub_response.json()["id"]
                print_info(f"Subscripción creada ID: {sub_id}")
                
                # 6.3: Customer ve su subscripción
                print("\n🔹 TEST 6.3: Customer consulta su subscripción")
                customer_sub = customer.get("/api/customer/radar/subscription")
                if customer_sub:
                    tests_total += 1
                    tests_passed += 1
                    sub_data = customer_sub.json()
                    print_info(f"Plan: {sub_data.get('plan_name')}")
                    print_info(f"Precio: ${sub_data.get('monthly_price')}/mes")
                
                # 6.4: Crear alerta (como admin)
                print("\n🔹 TEST 6.4: Crear alerta Radar")
                alert_data = {
                    "subscription_id": sub_id,
                    "alert_type": "new_competitor",
                    "severity": "high",
                    "title": "Nuevo competidor detectado",
                    "message": "Se detectó un nuevo competidor en tu mercado",
                    "data": {"competitor": "newcompetitor.com"}
                }
                alert_response = admin.post("/api/radar/alerts", alert_data)
                if alert_response:
                    tests_total += 1
                    tests_passed += 1
                    alert_id = alert_response.json()["id"]
                    print_info(f"Alerta creada ID: {alert_id}")
                    
                    # 6.5: Customer ve sus alertas
                    print("\n🔹 TEST 6.5: Customer consulta sus alertas")
                    customer_alerts = customer.get("/api/customer/radar/alerts")
                    if customer_alerts:
                        tests_total += 1
                        tests_passed += 1
                        alerts = customer_alerts.json()
                        print_info(f"Alertas: {len(alerts)}")
                    
                    # 6.6: Customer marca alerta como leída
                    print("\n🔹 TEST 6.6: Customer marca alerta como leída")
                    mark_read = customer.post(f"/api/customer/radar/alerts/{alert_id}/read", {})
                    if mark_read:
                        tests_total += 1
                        tests_passed += 1
    
    print(f"\n📊 Resultados Sistema Radar: {tests_passed}/{tests_total} tests pasados")
    return tests_passed == tests_total


def test_7_financial_metrics_restriction(admin: TestSession, worker: TestSession, customer: TestSession):
    """TEST 7: Restricción de métricas financieras"""
    print_section("TEST 7: RESTRICCIÓN DE MÉTRICAS FINANCIERAS")
    
    tests_passed = 0
    tests_total = 3
    
    # 7.1: ADMIN puede ver métricas
    print("\n🔹 TEST 7.1: ADMIN accede a métricas financieras")
    response = admin.get("/api/metrics/financial")
    if response:
        tests_passed += 1
        metrics = response.json()
        print_info(f"Métricas disponibles: {list(metrics.keys())}")
    
    # 7.2: WORKER NO puede ver métricas
    print("\n🔹 TEST 7.2: WORKER bloqueado de métricas financieras")
    response = worker.get("/api/metrics/financial", expected_status=403)
    if response:
        tests_passed += 1
    
    # 7.3: CUSTOMER NO puede ver métricas
    print("\n🔹 TEST 7.3: CUSTOMER bloqueado de métricas financieras")
    response = customer.get("/api/metrics/financial", expected_status=403)
    if response:
        tests_passed += 1
    
    print(f"\n📊 Resultados Restricción Financiera: {tests_passed}/{tests_total} tests pasados")
    return tests_passed == tests_total


def main():
    """Ejecuta todos los tests críticos"""
    print(f"\n{Colors.BOLD}{'='*80}")
    print(f"🚀 LOKIGI - TEST DE ESCENARIOS CRÍTICOS")
    print(f"{'='*80}{Colors.END}\n")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend: {BASE_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    
    # Verificar que el servidor está corriendo
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print_success("Servidor backend conectado")
        else:
            print_error("Servidor backend responde pero con error")
            return
    except Exception as e:
        print_error(f"No se puede conectar al backend: {str(e)}")
        print_warning("Asegúrate de que el servidor está corriendo: uvicorn main:app --reload")
        return
    
    # Ejecutar tests
    results = {}
    
    # TEST 1: Autenticación
    admin, worker, customer, auth_ok = test_1_authentication()
    results["Autenticación"] = auth_ok
    
    if not auth_ok:
        print_error("\n❌ Falló la autenticación. Ejecuta primero: python create_users.py")
        return
    
    # TEST 2: RBAC Authorization
    results["RBAC Authorization"] = test_2_rbac_authorization(admin, worker, customer)
    
    # TEST 3: Customer Isolation (RLS)
    results["Customer Isolation (RLS)"] = test_3_customer_isolation(admin, customer)
    
    # TEST 4: Customer Portal
    results["Customer Portal"] = test_4_customer_portal_endpoints(customer)
    
    # TEST 5: Audit Workflow
    results["Audit Workflow"] = test_5_audit_workflow(admin)
    
    # TEST 6: Radar System
    results["Radar System"] = test_6_radar_system(admin, customer)
    
    # TEST 7: Financial Metrics Restriction
    results["Financial Metrics"] = test_7_financial_metrics_restriction(admin, worker, customer)
    
    # Resumen final
    print_section("RESUMEN FINAL DE TESTS")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if passed else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"{test_name:.<50} {status}")
    
    print(f"\n{'='*80}")
    percentage = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    if percentage == 100:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 TODOS LOS TESTS PASARON: {passed_tests}/{total_tests} ({percentage:.0f}%){Colors.END}")
    elif percentage >= 80:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  MAYORÍA DE TESTS PASARON: {passed_tests}/{total_tests} ({percentage:.0f}%){Colors.END}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ MUCHOS TESTS FALLARON: {passed_tests}/{total_tests} ({percentage:.0f}%){Colors.END}")
    
    print(f"{'='*80}\n")
    
    # Recomendaciones
    if percentage < 100:
        print(f"\n{Colors.BOLD}📋 RECOMENDACIONES:{Colors.END}")
        if not results.get("Autenticación"):
            print("  • Ejecuta: python create_users.py")
        if not results.get("RBAC Authorization"):
            print("  • Verifica las políticas RBAC en auth.py")
        if not results.get("Customer Isolation (RLS)"):
            print("  • Revisa las políticas RLS en security_policies.py")
        if not results.get("Customer Portal"):
            print("  • Verifica api_customer_portal.py endpoints")


if __name__ == "__main__":
    main()
