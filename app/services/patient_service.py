import logging

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import AppException, ConflictException, NotFoundException, ServerException
from app.dtos.patient.patients import PatientCreateRequest, PatientResponse, PatientUpdateRequest
from app.repositories.patient_repository import PatientRepository


class PatientService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = PatientRepository(session)

    async def create_patient(self, request: PatientCreateRequest) -> PatientResponse:
        try:
            existing = await self.repo.find_one_by_external_id(request.patient_external_id)
            if existing:
                raise ConflictException(message=f"Patient {request.patient_external_id} already exists")

            patient = request.to_entity()
            patient = await self.repo.create(patient)
            return PatientResponse.from_entity(patient)
        except AppException:
            raise
        except Exception as e:
            logging.exception(f"Failed to create patient: {request.patient_external_id} - {str(e)}")
            raise ServerException(message="Failed to create patient")

    async def update_patient(self, patient_id: str, request: PatientUpdateRequest) -> PatientResponse:
        try:
            patient = await self.repo.find_one_by_external_id(patient_id)
            if not patient:
                raise NotFoundException(message=f"Patient {patient_id} not found")

            # Optimistic lock
            if patient.version != request.version:
                raise ConflictException(
                    message=f"Version conflict: expected {patient.version}, got {request.version}"
                )

            request.update_entity(patient)
            patient.version += 1

            patient = await self.repo.update(patient)
            return PatientResponse.from_entity(patient)
        except AppException:
            raise
        except Exception as e:
            logging.exception(f"Failed to update patient: {patient_id} - {str(e)}")
            raise ServerException(message="Failed to update patient")
