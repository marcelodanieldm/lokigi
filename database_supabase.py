"""
Configuración de Supabase (PostgreSQL) - Base de datos GRATIS
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

# Supabase connection string
# Format: postgresql://postgres:[PASSWORD]@[PROJECT_URL]:5432/postgres
SUPABASE_URL = os.getenv("SUPABASE_DB_URL")
DATABASE_URL = SUPABASE_URL if SUPABASE_URL else "sqlite:///./lokigi.db"

# Crear engine con configuración optimizada
if DATABASE_URL.startswith("postgresql"):
    # Configuración para Supabase/PostgreSQL
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Verifica conexión antes de usar
        pool_recycle=3600,   # Recicla conexiones cada hora
    )
else:
    # SQLite para desarrollo local
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency para FastAPI
    Usage:
        @app.get("/")
        def endpoint(db: Session = Depends(get_db)):
            # usar db aquí
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Inicializa la base de datos (crea todas las tablas)"""
    # Importar todos los modelos para que SQLAlchemy los conozca
    from models import User, Lead, Order, Task  # noqa
    
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    print(f"✅ Base de datos inicializada: {DATABASE_URL}")


def check_db_connection() -> bool:
    """Verifica que la conexión a la base de datos funcione"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return False
