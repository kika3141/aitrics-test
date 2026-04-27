from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy_utils import ChoiceType
from sqlmodel import Column, DateTime, Field, SQLModel, String, UniqueConstraint

from app.core.enums import BaseEnum
from app.models.base import (
    BaseCreatedUpdatedModel,
    BaseIntIDModel,
)


class VitalType(BaseEnum):
    HR = "HR"
    RR = "RR"
    SBP = "SBP"
    DBP = "DBP"
    SPO2 = "SpO2"
    BT = "BT"


class RiskLevel(BaseEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class VitalBase(SQLModel):
    patient_id: int = Field(foreign_key="patient.id", index=True)
    recorded_at: datetime = Field(sa_column=Column(DateTime, nullable=False))

    vital_type: VitalType = Field(
        sa_column=Column(
            ChoiceType(VitalType, impl=String()), nullable=False, index=True
        )
    )
    value: float


class Vital(VitalBase, BaseCreatedUpdatedModel, BaseIntIDModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "patient_id",
            "recorded_at",
            "vital_type",
            name="uix_vital_patient_id_recorded_at_vital_type",
        ),
    )


@dataclass(frozen=True)
class VitalRiskResult:
    """Vital 위험도 분석 결과 값객체"""

    risk_level: RiskLevel
    triggered_rules: list[str]
    vital_averages: dict[str, float]
    data_points_analyzed: int
    time_from: datetime
    time_to: datetime
    evaluated_at: datetime
