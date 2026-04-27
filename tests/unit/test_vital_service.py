from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictException, NotFoundException
from app.core.utils import utcnow
from app.dtos.vital.vitals import VitalUpsertRequest
from app.models.patient import Patient
from app.models.vital import Vital, VitalType
from app.services.vital_service import VitalService


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


def _make_vital(version: int = 1, value: float = 110.0) -> Vital:
    now = utcnow()
    return Vital(
        id=uuid4(),
        patient_id=1,
        recorded_at=datetime(2025, 12, 1, 10, 15),
        vital_type=VitalType.HR,
        value=value,
        version=version,
        created_at=now,
        updated_at=now,
    )


# ── Upsert (INSERT) ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_vital_insert(
    vital_service: VitalService, patient_repo: AsyncMock, vital_repo: AsyncMock
):
    """신규 Vital 등록 — 기존 데이터 없을 때 INSERT"""
    patient_repo.find_one_by_external_id.return_value = _make_patient()
    vital_repo.find_one_by_composite_key.return_value = None
    vital_repo.create.return_value = _make_vital(version=1)

    request = VitalUpsertRequest(
        patient_external_id="P001",
        recorded_at=datetime(2025, 12, 1, 10, 15),
        vital_type=VitalType.HR,
        value=110.0,
        version=1,
    )
    result, created = await vital_service.upsert_vital(request)

    assert result.version == 1
    assert created is True
    vital_repo.create.assert_called_once()
    vital_repo.update.assert_not_called()


# ── Upsert (UPDATE) ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_vital_update(
    vital_service: VitalService, patient_repo: AsyncMock, vital_repo: AsyncMock
):
    """기존 Vital 수정 — 버전 일치 시 UPDATE"""
    patient_repo.find_one_by_external_id.return_value = _make_patient()
    existing = _make_vital(version=1, value=110.0)
    vital_repo.find_one_by_composite_key.return_value = existing
    vital_repo.update.return_value = existing

    request = VitalUpsertRequest(
        patient_external_id="P001",
        recorded_at=datetime(2025, 12, 1, 10, 15),
        vital_type=VitalType.HR,
        value=120.0,
        version=1,
    )
    result, created = await vital_service.upsert_vital(request)

    # 버전 증가, 값 변경 확인
    assert result.version == 2
    assert result.value == 120.0
    assert created is False
    vital_repo.update.assert_called_once()
    vital_repo.create.assert_not_called()


# ── Upsert (Version Conflict) ────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_vital_version_conflict(
    vital_service: VitalService, patient_repo: AsyncMock, vital_repo: AsyncMock
):
    """버전 불일치 시 409 ConflictException"""
    patient_repo.find_one_by_external_id.return_value = _make_patient()
    vital_repo.find_one_by_composite_key.return_value = _make_vital(version=2)

    request = VitalUpsertRequest(
        patient_external_id="P001",
        recorded_at=datetime(2025, 12, 1, 10, 15),
        vital_type=VitalType.HR,
        value=999.0,
        version=1,
    )

    with pytest.raises(ConflictException):
        await vital_service.upsert_vital(request)

    vital_repo.update.assert_not_called()
    vital_repo.create.assert_not_called()


# ── Upsert (Patient Not Found) ───────────────────────────────


@pytest.mark.asyncio
async def test_upsert_vital_patient_not_found(
    vital_service: VitalService, patient_repo: AsyncMock, vital_repo: AsyncMock
):
    """존재하지 않는 환자에 Vital 등록 시 404"""
    patient_repo.find_one_by_external_id.return_value = None

    request = VitalUpsertRequest(
        patient_external_id="NONEXIST",
        recorded_at=datetime(2025, 12, 1, 10, 15),
        vital_type=VitalType.HR,
        value=110.0,
        version=1,
    )

    with pytest.raises(NotFoundException):
        await vital_service.upsert_vital(request)


# ── Get Vitals ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_patient_vitals_success(
    vital_service: VitalService, patient_repo: AsyncMock, vital_repo: AsyncMock
):
    """Vital 조회 성공"""
    patient_repo.find_one_by_external_id.return_value = _make_patient()
    vital_repo.find_by_patient_and_time_range.return_value = [
        _make_vital(value=80.0),
        _make_vital(value=85.0),
    ]

    result = await vital_service.get_patient_vitals(
        patient_external_id="P001",
        time_from=datetime(2025, 12, 1, 0, 0),
        time_to=datetime(2025, 12, 1, 23, 59),
        vital_type=VitalType.HR,
    )

    assert len(result.items) == 2
    assert result.patient_external_id == "P001"


@pytest.mark.asyncio
async def test_get_patient_vitals_patient_not_found(
    vital_service: VitalService, patient_repo: AsyncMock, vital_repo: AsyncMock
):
    """존재하지 않는 환자의 Vital 조회 시 404"""
    patient_repo.find_one_by_external_id.return_value = None

    with pytest.raises(NotFoundException):
        await vital_service.get_patient_vitals(
            patient_external_id="NONEXIST",
            time_from=datetime(2025, 12, 1, 0, 0),
            time_to=datetime(2025, 12, 1, 23, 59),
        )
