from datetime import date

from sqlalchemy_utils import ChoiceType
from sqlmodel import Column, Field, SQLModel, String, UniqueConstraint

from app.core.enums import Gender
from app.models.base import BaseCreatedUpdatedModel, BaseIntIDModel


class PatientBase(SQLModel):
    external_id: str = Field(max_length=20)
    name: str = Field(max_length=100)
    gender: Gender = Field(
        sa_column=Column(ChoiceType(Gender, impl=String()), nullable=False)
    )
    birth_date: date


class Patient(PatientBase, BaseCreatedUpdatedModel, BaseIntIDModel, table=True):
    __table_args__ = (UniqueConstraint("external_id", name="uix_patient_external_id"),)
