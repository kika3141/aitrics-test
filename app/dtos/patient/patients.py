from datetime import date, datetime

from pydantic import Field

from app.core.enums import Gender
from app.dtos.base import BaseDto
from app.models.patient import Patient


class PatientCreateRequest(BaseDto):
    model_config = {"populate_by_name": True}

    patient_external_id: str = Field(alias="patient_id")
    name: str
    gender: Gender
    birth_date: date

    def to_entity(self) -> Patient:
        return Patient(
            external_id=self.patient_external_id,
            name=self.name,
            gender=self.gender,
            birth_date=self.birth_date,
        )


class PatientUpdateRequest(BaseDto):
    name: str
    gender: Gender
    birth_date: date
    version: int

    def update_entity(self, entity: Patient) -> Patient:
        entity.name = self.name
        entity.gender = self.gender
        entity.birth_date = self.birth_date
        return entity


class PatientResponse(BaseDto):
    model_config = {"populate_by_name": True}

    patient_external_id: str = Field(serialization_alias="patient_id")
    name: str
    gender: Gender
    birth_date: date
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, entity: Patient) -> "PatientResponse":
        return cls(
            patient_external_id=entity.external_id,
            name=entity.name,
            gender=entity.gender,
            birth_date=entity.birth_date,
            version=entity.version,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
