from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.auth import verify_token
from app.core.database import get_session
from app.dtos.patient.patients_vitals import VitalRequestQuery, VitalResponse
from app.services.vital_service import VitalService

patients_vitals_router = APIRouter(tags=["vitals"], dependencies=[Depends(verify_token)])


@patients_vitals_router.get("", response_model=VitalResponse, response_model_exclude_none=True)
async def get_patient_vitals(
    patient_id: str,
    query: VitalRequestQuery = Query(...),
    session: AsyncSession = Depends(get_session),
) -> VitalResponse:
    service = VitalService(session)
    return await service.get_patient_vitals(
        patient_id,
        query.time_from,
        query.time_to,
        query.vital_type,
    )
