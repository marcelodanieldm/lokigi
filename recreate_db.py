"""
Script para recrear la base de datos con la nueva tabla Tasks
ADVERTENCIA: Esto eliminará TODOS los datos existentes
Solo usar en desarrollo
"""
import os
from database import Base, engine
from models import Lead, Order, Task, User

def recreate_database():
    """
    Elimina la base de datos actual y crea una nueva con todos los modelos
    """
    db_path = "lokigi.db"
    
    # Verificar si existe la DB
    if os.path.exists(db_path):
        print(f"⚠️  Base de datos '{db_path}' encontrada")
        confirm = input("¿Eliminar y recrear? Esto borrará TODOS los datos (s/n): ")
        
        if confirm.lower() != 's':
            print("❌ Operación cancelada")
            return
        
        # Eliminar DB
        os.remove(db_path)
        print(f"🗑️  Base de datos eliminada")
    
    # Crear todas las tablas
    print("📦 Creando todas las tablas...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Base de datos recreada exitosamente")
    print("\n📋 Tablas creadas:")
    print("   - leads")
    print("   - orders")
    print("   - tasks")
    print("   - users (NUEVA)")
    print("\n🚀 Puedes iniciar el servidor ahora: python main.py")

if __name__ == "__main__":
    print("=" * 60)
    print("RECREAR BASE DE DATOS - LOKIGI")
    print("=" * 60)
    print()
    
    recreate_database()
