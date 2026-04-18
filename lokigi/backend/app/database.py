from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


engine = None
SessionLocal = None


def init_engine(database_url: str | None = None) -> None:
    global engine
    global SessionLocal

    url = database_url or settings.database_url
    engine = create_engine(url, future=True, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


init_engine()


def get_db():
    if SessionLocal is None:
        raise RuntimeError("Database session factory is not initialized")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
