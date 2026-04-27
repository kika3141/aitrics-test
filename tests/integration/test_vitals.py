import pytest
from httpx import AsyncClient


@pytest.fixture
async def patient(client: AsyncClient):
    await client.post(
        "/api/v1/patients",
        json={
            "patient_id": "P00001234",
            "name": "John Doe",
            "gender": "M",
            "birth_date": "1975-03-01",
        },
    )


@pytest.mark.asyncio
async def test_create_vital(client: AsyncClient, patient):
    response = await client.post(
        "/api/v1/vitals",
        json={
            "patient_id": "P00001234",
            "recorded_at": "2025-12-01T10:15:00Z",
            "vital_type": "HR",
            "value": 110.0,
            "version": 1,
        },
    )
    assert response.status_code == 201
    assert response.json()["version"] == 1


@pytest.mark.asyncio
async def test_upsert_vital_update(client: AsyncClient, patient):
    payload = {
        "patient_id": "P00001234",
        "recorded_at": "2025-12-01T10:15:00Z",
        "vital_type": "HR",
        "value": 110.0,
        "version": 1,
    }
    await client.post("/api/v1/vitals", json=payload)

    # 정상 UPDATE
    payload["value"] = 120.0
    payload["version"] = 1
    response = await client.post("/api/v1/vitals", json=payload)
    assert response.status_code == 200
    assert response.json()["version"] == 2
    assert response.json()["value"] == 120.0


@pytest.mark.asyncio
async def test_upsert_vital_version_conflict(client: AsyncClient, patient):
    payload = {
        "patient_id": "P00001234",
        "recorded_at": "2025-12-01T10:15:00Z",
        "vital_type": "HR",
        "value": 110.0,
        "version": 1,
    }
    await client.post("/api/v1/vitals", json=payload)

    # 버전 충돌
    payload["value"] = 999.0
    payload["version"] = 999
    response = await client.post("/api/v1/vitals", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_vital_for_nonexistent_patient(client: AsyncClient):
    response = await client.post(
        "/api/v1/vitals",
        json={
            "patient_id": "NONEXIST",
            "recorded_at": "2025-12-01T10:15:00Z",
            "vital_type": "HR",
            "value": 110.0,
            "version": 1,
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_vitals(client: AsyncClient, patient):
    for i in range(3):
        await client.post(
            "/api/v1/vitals",
            json={
                "patient_id": "P00001234",
                "recorded_at": f"2025-12-01T10:{10 + i:02d}:00Z",
                "vital_type": "HR",
                "value": 80.0 + i,
                "version": 1,
            },
        )

    response = await client.get(
        "/api/v1/patients/P00001234/vitals",
        params={
            "from": "2025-12-01T00:00:00Z",
            "to": "2025-12-01T23:59:59Z",
            "vital_type": "HR",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
