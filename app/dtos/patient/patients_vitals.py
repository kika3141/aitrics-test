from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.dtos.base import BaseDto
from app.models.patient import Patient
from app.models.vital import Vital, VitalType


class VitalRequestQuery(BaseDto):
    model_config = {"populate_by_name": True}

    time_from: datetime = Field(alias="from")
    time_to: datetime = Field(alias="to")
    vital_type: VitalType | None = None


class VitalItem(BaseDto):
    recorded_at: datetime
    value: float


class VitalResponse(BaseDto):
    model_config = {"populate_by_name": True}

    patient_external_id: str = Field(serialization_alias="patient_id")
    vital_type: VitalType | None = None
    items: list[VitalItem]

    @classmethod
    def from_entity(
        cls, patient: Patient, vitals: list[Vital], vital_type: VitalType | None = None
    ) -> VitalResponse:
        """Vital 엔티티 목록 → 응답 DTO 변환"""
        items = [VitalItem(recorded_at=v.recorded_at, value=v.value) for v in vitals]
        return cls(patient_external_id=patient.external_id, vital_type=vital_type, items=items)
