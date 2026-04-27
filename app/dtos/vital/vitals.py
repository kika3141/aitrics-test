from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.dtos.base import BaseDto
from app.models.patient import Patient
from app.models.vital import Vital, VitalType


class VitalUpsertRequest(BaseDto):
    model_config = {"populate_by_name": True}

    patient_external_id: str = Field(alias="patient_id")
    recorded_at: datetime
    vital_type: VitalType
    value: float
    version: int

    def to_entity(self, patient_id: int) -> Vital:
        """외부 patient_id 대신 내부 PK를 받아 엔티티 생성"""
        return Vital(
            patient_id=patient_id,
            recorded_at=self.recorded_at,
            vital_type=self.vital_type,
            value=self.value,
            version=1,
        )

    def update_entity(self, entity: Vital) -> Vital:
        entity.value = self.value
        return entity


class VitalUpsertResponse(BaseDto):
    model_config = {"populate_by_name": True}

    patient_external_id: str = Field(serialization_alias="patient_id")
    recorded_at: datetime
    vital_type: VitalType
    value: float
    version: int

    @classmethod
    def from_entity(cls, entity: Vital, patient: Patient) -> VitalUpsertResponse:
        """Vital 엔티티 + Patient 엔티티 → 응답 생성"""
        return cls(
            patient_external_id=patient.external_id,
            recorded_at=entity.recorded_at,
            vital_type=entity.vital_type,
            value=entity.value,
            version=entity.version,
        )
