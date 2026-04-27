from fastapi import APIRouter, Depends, Response, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.auth import verify_token
from app.core.database import get_session
from app.dtos.vital.vitals import VitalUpsertRequest, VitalUpsertResponse
from app.services.vital_service import VitalService

vitals_router = APIRouter(tags=["vitals"], dependencies=[Depends(verify_token)])


@vitals_router.post("", response_model=VitalUpsertResponse, response_model_exclude_none=True)
async def upsert_vital(
    request: VitalUpsertRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> VitalUpsertResponse:
    service = VitalService(session)
    result, created = await service.upsert_vital(request)
    if created:
        response.status_code = status.HTTP_201_CREATED
    return result
