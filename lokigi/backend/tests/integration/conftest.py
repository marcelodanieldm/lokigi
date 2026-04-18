import uuid

import docker
import pytest
from fastapi.testclient import TestClient

testcontainers_postgres = pytest.importorskip(
    "testcontainers.postgres",
    reason="testcontainers is required for PostgreSQL integration tests",
)
PostgresContainer = testcontainers_postgres.PostgresContainer

from app import database
from app.config import settings
from app.main import app
from app.models import Base, User


TEST_FERNET_KEY = "8Q9w1N6f7q3i2B0v4R5t6Y7u8I9o0P1a2S3d4F5g6H="


@pytest.fixture(scope="session")
def postgres_url() -> str:
    try:
        docker.from_env().ping()
    except docker.errors.DockerException as exc:
        pytest.skip(f"Docker daemon unavailable for integration tests: {exc}")

    container = PostgresContainer("postgres:16")
    container.start()
    try:
        yield container.get_connection_url().replace("postgresql://", "postgresql+psycopg://")
    finally:
        container.stop()


@pytest.fixture(autouse=True)
def configure_app(postgres_url: str):
    settings.database_url = postgres_url
    settings.oauth_state_secret = "test-oauth-state-secret"
    settings.oauth_token_encryption_key = TEST_FERNET_KEY
    settings.google_client_id = "test-client-id"
    settings.google_client_secret = "test-client-secret"
    settings.google_redirect_uri = "http://testserver/oauth/google/callback"
    settings.google_pubsub_audience = "test-audience"

    database.init_engine(postgres_url)
    Base.metadata.drop_all(bind=database.engine)
    Base.metadata.create_all(bind=database.engine)

    yield

    Base.metadata.drop_all(bind=database.engine)


@pytest.fixture
def db_session():
    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_user(db_session):
    user = User(id=uuid.uuid4(), email="integration@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
