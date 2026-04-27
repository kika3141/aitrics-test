"""인증 실패 및 Validation 에러 통합 테스트"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite://"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)


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
async def no_auth_client(session: AsyncSession):
    """인증 override 없는 클라이언트 — verify_token이 실제로 실행됨"""

    async def override_session():
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    app.dependency_overrides[get_session] = override_session
    # verify_token override 하지 않음

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


# ── 인증 실패 (토큰 없음) ─────────────────────────────────────


@pytest.mark.asyncio
async def test_no_token_returns_401(no_auth_client: AsyncClient):
    """Authorization 헤더 없으면 401 Unauthorized"""
    response = await no_auth_client.post(
        "/api/v1/patients",
        json={
            "patient_id": "P001",
            "name": "홍길동",
            "gender": "M",
            "birth_date": "1975-03-01",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_invalid_token_returns_401(no_auth_client: AsyncClient):
    """잘못된 토큰이면 401 Unauthorized"""
    response = await no_auth_client.post(
        "/api/v1/patients",
        json={
            "patient_id": "P001",
            "name": "홍길동",
            "gender": "M",
            "birth_date": "1975-03-01",
        },
        headers={"Authorization": "Bearer wrong-token-value"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


# ── Validation 에러 (잘못된 요청 Body) ───────────────────────


@pytest.fixture
async def client(session: AsyncSession):
    """인증 override 포함 클라이언트"""
    from app.core.auth import verify_token

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


@pytest.mark.asyncio
async def test_create_patient_missing_fields(client: AsyncClient):
    """필수 필드 누락 시 422"""
    response = await client.post(
        "/api/v1/patients",
        json={"patient_id": "P001"},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["err_code"] == "UNPROCESSABLE_ENTITY"


@pytest.mark.asyncio
async def test_upsert_vital_invalid_type(client: AsyncClient):
    """유효하지 않은 vital_type이면 422"""
    response = await client.post(
        "/api/v1/vitals",
        json={
            "patient_id": "P001",
            "recorded_at": "2025-12-01T10:15:00Z",
            "vital_type": "INVALID_TYPE",
            "value": 110.0,
            "version": 1,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_inference_missing_patient_id(client: AsyncClient):
    """patient_id 누락 시 422"""
    response = await client.post(
        "/api/v1/inference/vital-risk",
        json={},
    )
    assert response.status_code == 422
