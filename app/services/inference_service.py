import logging
from collections import defaultdict
from datetime import timedelta

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException, NotFoundException, ServerException
from app.core.utils import utcnow
from app.dtos.inference.inference import InferenceResponse
from app.models.vital import RiskLevel, VitalRiskResult
from app.repositories.patient_repository import PatientRepository
from app.repositories.vital_repository import VitalRepository

RISK_RULES: list[tuple[str, str, float, str]] = [
    ("HR", ">", 120, "HR > 120"),
    ("SBP", "<", 90, "SBP < 90"),
    ("SpO2", "<", 90, "SpO2 < 90"),
]


class InferenceService:
    def __init__(self, session: AsyncSession) -> None:
        self.vital_repo = VitalRepository(session)
        self.patient_repo = PatientRepository(session)

    async def calculate_vital_risk(self, patient_external_id: str) -> InferenceResponse:
        try:
            patient = await self.patient_repo.find_one_by_external_id(patient_external_id)
            if not patient:
                raise NotFoundException(message=f"Patient {patient_external_id} not found")

            now = utcnow()
            time_from = now - timedelta(hours=settings.vital_risk_time_window_hours)

            # 외부 patient_id로 JOIN 조회
            vitals = await self.vital_repo.find_by_patient_and_time_range(
                patient_external_id, time_from, now
            )

            # Vital 타입별 평균 계산
            grouped: dict[str, list[float]] = defaultdict(list)
            for v in vitals:
                grouped[v.vital_type if isinstance(v.vital_type, str) else v.vital_type.value].append(v.value)

            vital_averages: dict[str, float] = {}
            for vtype, values in grouped.items():
                vital_averages[vtype] = round(sum(values) / len(values), 1)

            # 위험 규칙 평가
            triggered_rules: list[str] = []
            for vital_type, operator, threshold, label in RISK_RULES:
                avg = vital_averages.get(vital_type)
                if avg is None:
                    continue
                if operator == ">" and avg > threshold:
                    triggered_rules.append(label)
                elif operator == "<" and avg < threshold:
                    triggered_rules.append(label)

            # 위험 등급 결정
            count = len(triggered_rules)
            if count == 0:
                risk_level = RiskLevel.LOW
            elif count <= 2:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.HIGH

            result = VitalRiskResult(
                risk_level=risk_level,
                triggered_rules=triggered_rules,
                vital_averages=vital_averages,
                data_points_analyzed=len(vitals),
                time_from=time_from,
                time_to=now,
                evaluated_at=now,
            )

            return InferenceResponse.from_entity(patient, result)
        except AppException:
            raise
        except Exception as e:
            logging.exception(f"Failed to calculate vital risk: {patient_external_id} - {str(e)}")
            raise ServerException(message="Failed to calculate vital risk")
