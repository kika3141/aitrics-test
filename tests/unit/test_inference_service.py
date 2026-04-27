from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundException
from app.core.utils import utcnow
from app.models.patient import Patient
from app.models.vital import Vital, VitalType
from app.services.inference_service import InferenceService


def _make_patient() -> Patient:
    now = utcnow()
    return Patient(
        id=1,
        external_id="P001",
        name="홍길동",
        gender="M",
        birth_date=datetime(1975, 3, 1).date(),
        version=1,
        created_at=now,
        updated_at=now,
    )


def _make_vital(vital_type: VitalType, value: float, hours_ago: int = 0) -> Vital:
    now = utcnow()
    return Vital(
        id=uuid4(),
        patient_id=1,
        recorded_at=now - timedelta(hours=hours_ago),
        vital_type=vital_type,
        value=value,
        version=1,
        created_at=now,
        updated_at=now,
    )


# ── Risk Level: HIGH ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_calculate_vital_risk_high(
    inference_service: InferenceService, patient_repo: AsyncMock, vital_repo: AsyncMock
):
    """모든 위험 조건 충족 시 HIGH"""
    patient_repo.find_one_by_external_id.return_value = _make_patient()
    vital_repo.find_by_patient_and_time_range.return_value = [
        _make_vital(VitalType.HR, 130.0, hours_ago=1),
        _make_vital(VitalType.HR, 140.0, hours_ago=2),
        _make_vital(VitalType.SBP, 85.0, hours_ago=3),
        _make_vital(VitalType.SBP, 80.0, hours_ago=4),
        _make_vital(VitalType.SPO2, 88.0, hours_ago=5),
        _make_vital(VitalType.SPO2, 85.0, hours_ago=6),
    ]

    result = await inference_service.calculate_vital_risk("P001")

    assert result.risk_level == "HIGH"
    assert len(result.triggered_rules) == 3
    assert result.data_points_analyzed == 6
    assert result.vital_averages["HR"] == 135.0
    assert result.vital_averages["SBP"] == 82.5
    assert result.vital_averages["SpO2"] == 86.5


# ── Risk Level: LOW ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_calculate_vital_risk_low(
    inference_service: InferenceService, patient_repo: AsyncMock, vital_repo: AsyncMock
):
    """모든 수치 정상 시 LOW"""
    patient_repo.find_one_by_external_id.return_value = _make_patient()
    vital_repo.find_by_patient_and_time_range.return_value = [
        _make_vital(VitalType.HR, 70.0),
        _make_vital(VitalType.SBP, 120.0),
        _make_vital(VitalType.SPO2, 98.0),
    ]

    result = await inference_service.calculate_vital_risk("P001")

    assert result.risk_level == "LOW"
    assert len(result.triggered_rules) == 0
    assert result.data_points_analyzed == 3


# ── Risk Level: MEDIUM ────────────────────────────────────────


@pytest.mark.asyncio
async def test_calculate_vital_risk_medium(
    inference_service: InferenceService, patient_repo: AsyncMock, vital_repo: AsyncMock
):
    """일부 위험 조건만 충족 시 MEDIUM"""
    patient_repo.find_one_by_external_id.return_value = _make_patient()
    vital_repo.find_by_patient_and_time_range.return_value = [
        _make_vital(VitalType.HR, 130.0),  # HR > 120 → 위험
        _make_vital(VitalType.SBP, 120.0),  # SBP 정상
        _make_vital(VitalType.SPO2, 98.0),  # SpO2 정상
    ]

    result = await inference_service.calculate_vital_risk("P001")

    assert result.risk_level == "MEDIUM"
    assert len(result.triggered_rules) == 1
    assert "HR > 120" in result.triggered_rules


# ── No Vital Data ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_calculate_vital_risk_no_data(
    inference_service: InferenceService, patient_repo: AsyncMock, vital_repo: AsyncMock
):
    """Vital 데이터 없을 때 LOW (조건 충족 0개)"""
    patient_repo.find_one_by_external_id.return_value = _make_patient()
    vital_repo.find_by_patient_and_time_range.return_value = []

    result = await inference_service.calculate_vital_risk("P001")

    assert result.risk_level == "LOW"
    assert len(result.triggered_rules) == 0
    assert result.data_points_analyzed == 0


# ── Patient Not Found ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_calculate_vital_risk_patient_not_found(
    inference_service: InferenceService, patient_repo: AsyncMock
):
    """존재하지 않는 환자 시 404"""
    patient_repo.find_one_by_external_id.return_value = None

    with pytest.raises(NotFoundException):
        await inference_service.calculate_vital_risk("NONEXIST")


# ── Boundary: 경계값 테스트 ───────────────────────────────────


@pytest.mark.asyncio
async def test_calculate_vital_risk_boundary_values(
    inference_service: InferenceService, patient_repo: AsyncMock, vital_repo: AsyncMock
):
    """경계값 (HR=120, SBP=90, SpO2=90) — 조건 미충족으로 LOW"""
    patient_repo.find_one_by_external_id.return_value = _make_patient()
    vital_repo.find_by_patient_and_time_range.return_value = [
        _make_vital(VitalType.HR, 120.0),   # HR > 120 이 아니라 == 120 → 미충족
        _make_vital(VitalType.SBP, 90.0),   # SBP < 90 이 아니라 == 90 → 미충족
        _make_vital(VitalType.SPO2, 90.0),  # SpO2 < 90 이 아니라 == 90 → 미충족
    ]

    result = await inference_service.calculate_vital_risk("P001")

    assert result.risk_level == "LOW"
    assert len(result.triggered_rules) == 0
