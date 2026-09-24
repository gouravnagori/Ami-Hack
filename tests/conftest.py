from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.clock import FrozenClock
from app.core.config import Role
from app.core.deps import get_clock, get_db
from app.core.security import create_access_token
from app.db.base import Base
from app.main import app

# In-memory test database
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)

test_session_maker = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
async def init_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
def frozen_clock() -> FrozenClock:
    return FrozenClock()


@pytest.fixture
async def client(
    db_session: AsyncSession, frozen_clock: FrozenClock
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    def override_get_clock():
        return frozen_clock

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_clock] = override_get_clock

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def donor_token() -> str:
    return create_access_token("11111111-1111-1111-1111-111111111111", Role.DONOR)


@pytest.fixture
def recipient_token() -> str:
    return create_access_token("22222222-2222-2222-2222-222222222222", Role.RECIPIENT)


@pytest.fixture
def driver_token() -> str:
    return create_access_token("33333333-3333-3333-3333-333333333333", Role.DRIVER)
