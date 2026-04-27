from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.auth import verify_token
from app.core.database import get_session
from app.dtos.inference.inference import InferenceRequest, InferenceResponse
from app.services.inference_service import InferenceService

inference_router = APIRouter(tags=["inference"], dependencies=[Depends(verify_token)])


@inference_router.post("/vital-risk", response_model=InferenceResponse, response_model_exclude_none=True)
async def calculate_vital_risk(
    request: InferenceRequest,
    session: AsyncSession = Depends(get_session),
) -> InferenceResponse:
    service = InferenceService(session)
    return await service.calculate_vital_risk(request.patient_external_id)
