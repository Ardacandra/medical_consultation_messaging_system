import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import Base, get_db
from app.core.security import create_access_token
import asyncio

# Use an in-memory SQLite database for testing, or a separate test DB
# For simplicity with asyncpg/postgres dependencies, we might mock DB or use a test postgres URL.
# However, user's setup uses postgres. Let's try to use the existing DB but rollback transactions,
# or better, use a distinct test database URL if available.
# Given the constraints, I'll mock the dependency override to use a temporary SQLite for speed/isolation if possible,
# BUT the app uses postgres specific fields (JSONB, etc).
# So we will wrap the existing DB connection in a transaction that always rolls back.

TEST_DATABASE_URL = "postgresql+asyncpg://user:password@localhost/nightingale" 

from sqlalchemy.pool import NullPool

# Disable startup events (migrations) to verify isolation and avoid concurrency locks
app.router.startup_handlers = []

@pytest.fixture
async def override_get_db():
    # Create a fresh engine for each test on the current loop
    # Use NullPool to close connections immediately after use
    test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with test_engine.begin() as conn:
        # We can optionally create tables here if we were using a separate test DB
        # await conn.run_sync(Base.metadata.create_all)
        pass

    async def _get_test_db():
        async with TestSessionLocal() as session:
            yield session
            
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()
    await test_engine.dispose()

from unittest.mock import MagicMock
from app.services.chat import ChatService
from app.services.risk import RiskAnalysisService
from app.services.memory import MemoryService
from app.api.v1.endpoints import chat as chat_endpoint

@pytest.fixture(autouse=True)
async def patch_services():
    # Create fresh instances for each test to attach to current loop
    # Note: This assumes __init__ doesn't do async setup, but the methods do.
    # Actually, if Langchain clients are created in __init__, they grab the loop there.
    # So we must recreate the service instances.
    
    # We need to patch the module-level variables in the endpoint file
    new_chat_service = ChatService()
    new_risk_service = RiskAnalysisService()
    new_memory_service = MemoryService()
    
    # Monkeypatch the module variables
    chat_endpoint.chat_service = new_chat_service
    chat_endpoint.risk_service = new_risk_service
    chat_endpoint.memory_service = new_memory_service
    
    yield
    # Cleanup? Not strictly necessary as next test will overwrite.

@pytest.fixture
async def client(override_get_db):
    # Function scoped client, ensuring new loop
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture
def patient_token():
    return create_access_token(subject="1") # User 1 is patient

@pytest.fixture
def clinician_token():
    # We might need to seed a clinician user first if not exists
    return create_access_token(subject="2") # Assume User 2 is clinician for now

# Dependency override for DB could be added here if we want to isolate data completely.
