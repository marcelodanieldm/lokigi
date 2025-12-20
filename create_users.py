"""
Script para crear usuarios del backoffice
"""
from database import SessionLocal
from models import UserRole
from auth import create_user

def setup_initial_users():
    """Crea usuarios iniciales para testing"""
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("CREAR USUARIOS DEL BACKOFFICE")
        print("=" * 70)
        print()
        
        # Crear superusuario
        try:
            superuser = create_user(
                email="admin@lokigi.com",
                password="admin123",  # Cambiar en producción
                full_name="Administrador",
                role=UserRole.SUPERUSER,
                db=db
            )
            print("✅ Superusuario creado:")
            print(f"   Email: {superuser.email}")
            print(f"   Password: admin123")
            print(f"   Rol: {superuser.role.value}")
            print()
        except ValueError as e:
            print(f"⚠️  Superusuario ya existe: {e}")
            print()
        
        # Crear trabajador
        try:
            worker = create_user(
                email="trabajo@lokigi.com",
                password="trabajo123",  # Cambiar en producción
                full_name="Usuario Trabajo",
                role=UserRole.WORKER,
                db=db
            )
            print("✅ Trabajador creado:")
            print(f"   Email: {worker.email}")
            print(f"   Password: trabajo123")
            print(f"   Rol: {worker.role.value}")
            print()
        except ValueError as e:
            print(f"⚠️  Trabajador ya existe: {e}")
            print()
        
        print("=" * 70)
        print("✅ USUARIOS LISTOS PARA USAR")
        print("=" * 70)
        print()
        print("🔐 Credenciales de acceso:")
        print()
        print("SUPERUSUARIO (acceso total):")
        print("  Email: admin@lokigi.com")
        print("  Password: admin123")
        print("  Dashboard: http://localhost:3000/dashboard")
        print()
        print("TRABAJADOR (solo Work Queue):")
        print("  Email: trabajo@lokigi.com")
        print("  Password: trabajo123")
        print("  Dashboard: http://localhost:3000/dashboard/work")
        print()
        print("=" * 70)
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
