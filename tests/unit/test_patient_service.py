from datetime import date
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ConflictException, NotFoundException
from app.core.utils import utcnow
from app.dtos.patient.patients import PatientCreateRequest, PatientUpdateRequest
from app.models.patient import Patient
from app.services.patient_service import PatientService

# ── Create ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_patient_success(patient_service: PatientService, patient_repo: AsyncMock):
    """신규 환자 등록 성공"""
    patient_repo.find_one_by_external_id.return_value = None

    now = utcnow()
    patient_repo.create.return_value = Patient(
        id=1,
        external_id="P001",
        name="홍길동",
        gender="M",
        birth_date=date(1975, 3, 1),
        version=1,
        created_at=now,
        updated_at=now,
    )

    request = PatientCreateRequest(
        patient_external_id="P001",
        name="홍길동",
        gender="M",
        birth_date=date(1975, 3, 1),
    )
    result = await patient_service.create_patient(request)

    assert result.patient_external_id == "P001"
    assert result.version == 1
    patient_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_patient_duplicate(patient_service: PatientService, patient_repo: AsyncMock):
    """이미 존재하는 환자 ID로 등록 시 409"""
    patient_repo.find_one_by_external_id.return_value = Patient(
        id=1,
        external_id="P001",
        name="홍길동",
        gender="M",
        birth_date=date(1975, 3, 1),
        version=1,
        created_at=utcnow(),
        updated_at=utcnow(),
    )

    request = PatientCreateRequest(
        patient_external_id="P001",
        name="홍길동",
        gender="M",
        birth_date=date(1975, 3, 1),
    )

    with pytest.raises(ConflictException):
        await patient_service.create_patient(request)

    patient_repo.create.assert_not_called()


# ── Update ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_patient_success(patient_service: PatientService, patient_repo: AsyncMock):
    """정상 업데이트 — 버전 일치"""
    now = utcnow()
    existing = Patient(
        id=1,
        external_id="P001",
        name="홍길동",
        gender="M",
        birth_date=date(1975, 3, 1),
        version=1,
        created_at=now,
        updated_at=now,
    )
    patient_repo.find_one_by_external_id.return_value = existing
    patient_repo.update.return_value = existing

    request = PatientUpdateRequest(
        name="김철수",
        gender="M",
        birth_date=date(1975, 3, 1),
        version=1,
    )
    result = await patient_service.update_patient("P001", request)

    assert result.version == 2
    patient_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_patient_version_conflict(patient_service: PatientService, patient_repo: AsyncMock):
    """버전 불일치 시 409 ConflictException"""
    patient_repo.find_one_by_external_id.return_value = Patient(
        id=1,
        external_id="P001",
        name="홍길동",
        gender="M",
        birth_date=date(1975, 3, 1),
        version=2,
        created_at=utcnow(),
        updated_at=utcnow(),
    )

    request = PatientUpdateRequest(
        name="김철수",
        gender="M",
        birth_date=date(1975, 3, 1),
        version=1,
    )

    with pytest.raises(ConflictException):
        await patient_service.update_patient("P001", request)

    patient_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_patient_not_found(patient_service: PatientService, patient_repo: AsyncMock):
    """존재하지 않는 환자 수정 시 404"""
    patient_repo.find_one_by_external_id.return_value = None

    request = PatientUpdateRequest(
        name="김철수",
        gender="M",
        birth_date=date(1990, 1, 1),
        version=1,
    )

    with pytest.raises(NotFoundException):
        await patient_service.update_patient("NONEXIST", request)
