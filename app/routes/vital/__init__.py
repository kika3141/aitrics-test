from fastapi import APIRouter

from app.routes.vital.vitals import vitals_router

base_v1_vital_router = APIRouter(prefix="/v1")
base_v1_vital_router.include_router(router=vitals_router, prefix="/vitals")

base_vital_router = APIRouter()
base_vital_router.include_router(router=base_v1_vital_router)
