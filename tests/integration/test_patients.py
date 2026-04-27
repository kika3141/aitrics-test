import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_patient(client: AsyncClient):
    response = await client.post(
        "/api/v1/patients",
        json={
            "patient_id": "P00001234",
            "name": "John Doe",
            "gender": "M",
            "birth_date": "1975-03-01",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["patient_id"] == "P00001234"
    assert data["version"] == 1


@pytest.mark.asyncio
async def test_create_duplicate_patient(client: AsyncClient):
    payload = {
        "patient_id": "P00001234",
        "name": "John Doe",
        "gender": "M",
        "birth_date": "1975-03-01",
    }
    await client.post("/api/v1/patients", json=payload)
    response = await client.post("/api/v1/patients", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_patient_optimistic_lock(client: AsyncClient):
    await client.post(
        "/api/v1/patients",
        json={
            "patient_id": "P00001234",
            "name": "John Doe",
            "gender": "M",
            "birth_date": "1975-03-01",
        },
    )

    # 정상 업데이트
    response = await client.put(
        "/api/v1/patients/P00001234",
        json={
            "name": "Jane Doe",
            "gender": "F",
            "birth_date": "1975-03-01",
            "version": 1,
        },
    )
    assert response.status_code == 200
    assert response.json()["version"] == 2

    # 버전 충돌
    response = await client.put(
        "/api/v1/patients/P00001234",
        json={
            "name": "Stale Update",
            "gender": "M",
            "birth_date": "1975-03-01",
            "version": 1,
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_patient_not_found(client: AsyncClient):
    response = await client.put(
        "/api/v1/patients/NONEXIST",
        json={
            "name": "Nobody",
            "gender": "M",
            "birth_date": "1990-01-01",
            "version": 1,
        },
    )
    assert response.status_code == 404
