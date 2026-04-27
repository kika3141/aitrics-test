from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.auth import verify_token
from app.core.database import get_session
from app.dtos.patient.patients import PatientCreateRequest, PatientResponse, PatientUpdateRequest
from app.services.patient_service import PatientService

patients_router = APIRouter(tags=["patients"], dependencies=[Depends(verify_token)])


@patients_router.post("", response_model=PatientResponse, response_model_exclude_none=True, status_code=status.HTTP_201_CREATED)
async def create_patient(
    request: PatientCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> PatientResponse:
    service = PatientService(session)
    return await service.create_patient(request)


@patients_router.put("/{patient_id}", response_model=PatientResponse, response_model_exclude_none=True)
async def update_patient(
    patient_id: str,
    request: PatientUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> PatientResponse:
    service = PatientService(session)
    return await service.update_patient(patient_id, request)
