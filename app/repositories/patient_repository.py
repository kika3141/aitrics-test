from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.patient import Patient


class PatientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_one_by_external_id(self, external_id: str) -> Patient | None:
        statement = select(Patient).where(Patient.external_id == external_id)
        result = await self.session.exec(statement)
        return result.one_or_none()

    async def create(self, patient: Patient) -> Patient:
        self.session.add(patient)
        await self.session.flush()
        return patient

    async def update(self, patient: Patient) -> Patient:
        self.session.add(patient)
        await self.session.flush()
        return patient
