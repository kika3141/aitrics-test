import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.auth import verify_token
from app.core.database import get_session
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite://"

engine = create_async_engine(TEST_DATABASE_URL, echo=True)


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def session():
    async with AsyncSession(engine) as session:
        yield session


@pytest.fixture
async def client(session: AsyncSession):
    async def override_session():
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    async def override_token():
        return "test-token"

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[verify_token] = override_token

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()
