"""서비스 계층 예외 처리 테스트 — except Exception → ServerException 변환"""

from datetime import date, datetime
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ServerException
from app.core.utils import utcnow
from app.dtos.patient.patients import PatientCreateRequest, PatientUpdateRequest
from app.dtos.vital.vitals import VitalUpsertRequest
from app.models.patient import Patient
from app.models.vital import VitalType
from app.services.inference_service import InferenceService
from app.services.patient_service import PatientService
from app.services.vital_service import VitalService


def _make_patient() -> Patient:
    now = utcnow()
    return Patient(
        id=1,
        external_id="P001",
        name="홍길동",
        gender="M",
        birth_date=date(1975, 3, 1),
        version=1,
        created_at=now,
        updated_at=now,
    )


# ── PatientService ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_patient_unexpected_error(
    patient_service: PatientService, patient_repo: AsyncMock
):
    """create_patient에서 예상치 못한 예외 발생 시 ServerException"""
    patient_repo.find_one_by_external_id.return_value = None
    patient_repo.create.side_effect = RuntimeError("DB connection failed")

    request = PatientCreateRequest(
        patient_external_id="P001", name="홍길동", gender="M", birth_date=date(1975, 3, 1)
    )

    with pytest.raises(ServerException):
        await patient_service.create_patient(request)


@pytest.mark.asyncio
async def test_update_patient_unexpected_error(
    patient_service: PatientService, patient_repo: AsyncMock
):
    """update_patient에서 예상치 못한 예외 발생 시 ServerException"""
    patient_repo.find_one_by_external_id.return_value = _make_patient()
    patient_repo.update.side_effect = RuntimeError("DB connection failed")

    request = PatientUpdateRequest(
        name="김철수", gender="M", birth_date=date(1975, 3, 1), version=1
    )

    with pytest.raises(ServerException):
        await patient_service.update_patient("P001", request)


# ���─ VitalService ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_vital_unexpected_error(
    vital_service: VitalService, patient_repo: AsyncMock, vital_repo: AsyncMock
):
    """upsert_vital에서 예상치 못한 예외 발생 시 ServerException"""
    patient_repo.find_one_by_external_id.return_value = _make_patient()
    vital_repo.find_one_by_composite_key.side_effect = RuntimeError("DB error")

    request = VitalUpsertRequest(
        patient_external_id="P001",
        recorded_at=datetime(2025, 12, 1, 10, 15),
        vital_type=VitalType.HR,
        value=110.0,
        version=1,
    )

    with pytest.raises(ServerException):
        await vital_service.upsert_vital(request)


@pytest.mark.asyncio
async def test_get_patient_vitals_unexpected_error(
    vital_service: VitalService, patient_repo: AsyncMock, vital_repo: AsyncMock
):
    """get_patient_vitals에서 예상치 못한 예외 발생 시 ServerException"""
    patient_repo.find_one_by_external_id.return_value = _make_patient()
    vital_repo.find_by_patient_and_time_range.side_effect = RuntimeError("DB error")

    with pytest.raises(ServerException):
        await vital_service.get_patient_vitals(
            patient_external_id="P001",
            time_from=datetime(2025, 12, 1, 0, 0),
            time_to=datetime(2025, 12, 1, 23, 59),
        )


# ── InferenceService ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_calculate_vital_risk_unexpected_error(
    inference_service: InferenceService, patient_repo: AsyncMock, vital_repo: AsyncMock
):
    """calculate_vital_risk에서 예상치 못한 예외 발생 ��� ServerException"""
    patient_repo.find_one_by_external_id.return_value = _make_patient()
    vital_repo.find_by_patient_and_time_range.side_effect = RuntimeError("DB error")

    with pytest.raises(ServerException):
        await inference_service.calculate_vital_risk("P001")
