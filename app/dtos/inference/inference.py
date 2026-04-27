from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.dtos.base import BaseDto
from app.models.patient import Patient
from app.models.vital import RiskLevel, VitalRiskResult


class InferenceRequest(BaseDto):
    model_config = {"populate_by_name": True}

    patient_external_id: str = Field(alias="patient_id")


class TimeRange(BaseDto):
    model_config = {"populate_by_name": True}

    time_from: datetime = Field(serialization_alias="from")
    time_to: datetime = Field(serialization_alias="to")


class InferenceResponse(BaseDto):
    model_config = {"populate_by_name": True}

    patient_external_id: str = Field(serialization_alias="patient_id")
    risk_level: RiskLevel
    triggered_rules: list[str]
    vital_averages: dict[str, float]
    data_points_analyzed: int
    time_range: TimeRange
    evaluated_at: datetime

    @classmethod
    def from_entity(cls, patient: Patient, result: VitalRiskResult) -> InferenceResponse:
        """Patient 엔티티 + 분석 결과 값객체 → 응답 생성"""
        return cls(
            patient_external_id=patient.external_id,
            risk_level=result.risk_level,
            triggered_rules=result.triggered_rules,
            vital_averages=result.vital_averages,
            data_points_analyzed=result.data_points_analyzed,
            time_range=TimeRange(time_from=result.time_from, time_to=result.time_to),
            evaluated_at=result.evaluated_at,
        )
