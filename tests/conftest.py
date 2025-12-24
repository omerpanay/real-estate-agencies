"""
Pytest configuration and fixtures for async testing.
"""
import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.tenant import Tenant, User


# Use SQLite for testing (in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with database session override."""
    
    async def override_get_db():
        yield test_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def tenant_a(test_session: AsyncSession) -> Tenant:
    """Create Tenant A for testing."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Tenant A - Real Estate",
        slug="tenant-a",
        is_active=True,
    )
    test_session.add(tenant)
    await test_session.commit()
    await test_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def tenant_b(test_session: AsyncSession) -> Tenant:
    """Create Tenant B for testing."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Tenant B - Clinic",
        slug="tenant-b",
        is_active=True,
    )
    test_session.add(tenant)
    await test_session.commit()
    await test_session.refresh(tenant)
    return tenant


@pytest_asyncio.fixture
async def user_a(test_session: AsyncSession, tenant_a: Tenant) -> User:
    """Create User A belonging to Tenant A."""
    user = User(
        id=uuid.uuid4(),
        email="user_a@tenanta.com",
        hashed_password=hash_password("password123"),
        full_name="User A",
        is_active=True,
        tenant_id=tenant_a.id,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_b(test_session: AsyncSession, tenant_b: Tenant) -> User:
    """Create User B belonging to Tenant B."""
    user = User(
        id=uuid.uuid4(),
        email="user_b@tenantb.com",
        hashed_password=hash_password("password123"),
        full_name="User B",
        is_active=True,
        tenant_id=tenant_b.id,
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


async def get_auth_token(client: AsyncClient, email: str, password: str) -> str:
    """Helper to get authentication token."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]
