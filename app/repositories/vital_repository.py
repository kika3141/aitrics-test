from datetime import datetime

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.patient import Patient
from app.models.vital import Vital, VitalType


class VitalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_patient_and_time_range(
        self,
        patient_external_id: str,
        time_from: datetime,
        time_to: datetime,
        vital_type: VitalType | None = None,
    ) -> list[Vital]:
        """외부 patient_id로 Patient JOIN하여 Vital 조회"""
        statement = (
            select(Vital)
            .join(Patient, Vital.patient_id == Patient.id)
            .where(
                Patient.external_id == patient_external_id,
                Vital.recorded_at >= time_from,
                Vital.recorded_at <= time_to,
            )
        )
        if vital_type:
            statement = statement.where(Vital.vital_type == vital_type)
        statement = statement.order_by(Vital.recorded_at)
        result = await self.session.exec(statement)
        return list(result.all())

    async def find_one_by_composite_key(
        self,
        patient_external_id: str,
        recorded_at: datetime,
        vital_type: VitalType,
    ) -> Vital | None:
        """외부 patient_id로 Patient JOIN하여 복합키 조회"""
        statement = (
            select(Vital)
            .join(Patient, Vital.patient_id == Patient.id)
            .where(
                Patient.external_id == patient_external_id,
                Vital.recorded_at == recorded_at,
                Vital.vital_type == vital_type,
            )
        )
        result = await self.session.exec(statement)
        return result.one_or_none()

    async def create(self, vital: Vital) -> Vital:
        self.session.add(vital)
        await self.session.flush()
        return vital

    async def update(self, vital: Vital) -> Vital:
        self.session.add(vital)
        await self.session.flush()
        return vital
