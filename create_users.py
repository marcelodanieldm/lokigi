"""
Script para crear usuarios del backoffice con sistema RBAC
"""
from database import SessionLocal
from models import UserRole, Lead
from auth import create_user

def setup_initial_users():
    """Crea usuarios iniciales para testing con los 3 roles: ADMIN, WORKER, CUSTOMER"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("CREAR USUARIOS DEL SISTEMA RBAC - LOKIGI")
        print("=" * 80)
        print()
        
        # Crear ADMIN (acceso total a todo el sistema)
        try:
            admin = create_user(
                email="admin@lokigi.com",
                password="admin123",  # Cambiar en producción
                full_name="Daniel - Administrador",
                role=UserRole.ADMIN,
                db=db
            )
            print("✅ ADMIN creado:")
            print(f"   Email: {admin.email}")
            print(f"   Password: admin123")
            print(f"   Rol: {admin.role.value}")
            print(f"   Permisos: Acceso total - métricas, exportación, gestión de pagos")
            print()
        except ValueError as e:
            print(f"⚠️  ADMIN ya existe: {e}")
            print()
        
        # Crear WORKER (acceso a Work Queue, sin métricas financieras)
        try:
            worker = create_user(
                email="worker@lokigi.com",
                password="worker123",  # Cambiar en producción
                full_name="Trabajador - Cola de Tareas",
                role=UserRole.WORKER,
                db=db
            )
            print("✅ WORKER creado:")
            print(f"   Email: {worker.email}")
            print(f"   Password: worker123")
            print(f"   Rol: {worker.role.value}")
            print(f"   Permisos: Work Queue, ver tareas, SIN acceso a métricas financieras")
            print()
        except ValueError as e:
            print(f"⚠️  WORKER ya existe: {e}")
            print()
        
        # Crear lead de prueba para vincular al CUSTOMER
        test_lead = db.query(Lead).filter(Lead.email == "cliente@example.com").first()
        if not test_lead:
            test_lead = Lead(
                nombre="Cliente Demo",
                email="cliente@example.com",
                telefono="+34600123456",
                whatsapp="+34600123456",
                nombre_negocio="Empresa Demo S.A.",
                customer_status="lead"
            )
            db.add(test_lead)
            db.commit()
            db.refresh(test_lead)
            print("✅ Lead de prueba creado para vincular al CUSTOMER")
            print(f"   Empresa: {test_lead.nombre_negocio}")
            print(f"   Email: {test_lead.email}")
            print()
        
        # Crear CUSTOMER (solo ve sus propios reportes y pagos)
        try:
            customer = create_user(
                email="cliente@example.com",
                password="cliente123",  # Cambiar en producción
                full_name="Cliente Demo",
                role=UserRole.CUSTOMER,
                customer_lead_id=test_lead.id,  # Vincular al lead
                db=db
            )
            print("✅ CUSTOMER creado:")
            print(f"   Email: {customer.email}")
            print(f"   Password: cliente123")
            print(f"   Rol: {customer.role.value}")
            print(f"   Lead vinculado: {test_lead.nombre_negocio} (ID: {test_lead.id})")
            print(f"   Permisos: Solo ve sus propios reportes, pagos, tareas y alertas Radar")
            print()
        except ValueError as e:
            print(f"⚠️  CUSTOMER ya existe: {e}")
            print()
        
        print("=" * 80)
        print("✅ SISTEMA RBAC CONFIGURADO - USUARIOS LISTOS")
        print("=" * 80)
        print()
        print("🔐 Credenciales de acceso:")
        print()
        print("1️⃣  ADMIN (Daniel - Acceso Total):")
        print("    Email: admin@lokigi.com")
        print("    Password: admin123")
        print("    Dashboard: http://localhost:3000/dashboard")
        print("    Acceso: ✅ Métricas ✅ Exportar ✅ Pagos ✅ Usuarios")
        print()
        print("2️⃣  WORKER (Trabajador - Work Queue):")
        print("    Email: worker@lokigi.com")
        print("    Password: worker123")
        print("    Dashboard: http://localhost:3000/dashboard/work")
        print("    Acceso: ✅ Work Queue ✅ Tareas ❌ Métricas Financieras")
        print()
        print("3️⃣  CUSTOMER (Cliente - Portal Propio):")
        print("    Email: cliente@example.com")
        print("    Password: cliente123")
        print("    Portal: http://localhost:3000/customer")
        print("    Acceso: ✅ Sus reportes ✅ Sus pagos ✅ Sus tareas ✅ Radar")
        print("    Restricción: ❌ NO puede ver datos de otros clientes")
        print()
        print("=" * 80)
        print()
        print("📋 API Endpoints disponibles:")
        print()
        print("CUSTOMER Portal:")
        print("  GET  /api/customer/me - Perfil del cliente")
        print("  GET  /api/customer/reports - Reportes de auditoría")
        print("  GET  /api/customer/orders - Historial de pagos")
        print("  GET  /api/customer/tasks - Tareas de sus órdenes")
        print("  GET  /api/customer/radar/subscription - Estado de Radar")
        print("  GET  /api/customer/radar/alerts - Alertas de Radar")
        print("  GET  /api/customer/dashboard/summary - Dashboard resumen")
        print()
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    setup_initial_users()
