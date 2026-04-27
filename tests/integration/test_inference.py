from datetime import timedelta

import pytest
from httpx import AsyncClient

from app.core.utils import utcnow


@pytest.fixture
async def patient_with_vitals(client: AsyncClient):
    await client.post(
        "/api/v1/patients",
        json={
            "patient_id": "P00001234",
            "name": "John Doe",
            "gender": "M",
            "birth_date": "1975-03-01",
        },
    )

    now = utcnow()
    vitals = [
        ("HR", 130.0),
        ("HR", 140.0),
        ("SBP", 85.0),
        ("SBP", 80.0),
        ("SpO2", 88.0),
        ("SpO2", 85.0),
    ]
    for i, (vtype, value) in enumerate(vitals):
        await client.post(
            "/api/v1/vitals",
            json={
                "patient_id": "P00001234",
                "recorded_at": (now - timedelta(hours=i)).isoformat(),
                "vital_type": vtype,
                "value": value,
                "version": 1,
            },
        )


@pytest.mark.asyncio
async def test_inference_high_risk(client: AsyncClient, patient_with_vitals):
    response = await client.post(
        "/api/v1/inference/vital-risk",
        json={"patient_id": "P00001234"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "HIGH"
    assert len(data["triggered_rules"]) == 3
    assert data["data_points_analyzed"] == 6


@pytest.mark.asyncio
async def test_inference_low_risk(client: AsyncClient):
    await client.post(
        "/api/v1/patients",
        json={
            "patient_id": "P00002222",
            "name": "Healthy Person",
            "gender": "F",
            "birth_date": "1990-01-01",
        },
    )

    now = utcnow()
    vitals = [("HR", 70.0), ("SBP", 120.0), ("SpO2", 98.0)]
    for i, (vtype, value) in enumerate(vitals):
        await client.post(
            "/api/v1/vitals",
            json={
                "patient_id": "P00002222",
                "recorded_at": (now - timedelta(hours=i)).isoformat(),
                "vital_type": vtype,
                "value": value,
                "version": 1,
            },
        )

    response = await client.post(
        "/api/v1/inference/vital-risk",
        json={"patient_id": "P00002222"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "LOW"
    assert len(data["triggered_rules"]) == 0


@pytest.mark.asyncio
async def test_inference_patient_not_found(client: AsyncClient):
    response = await client.post(
        "/api/v1/inference/vital-risk",
        json={"patient_id": "NONEXIST"},
    )
    assert response.status_code == 404
