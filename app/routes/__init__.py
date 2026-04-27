from fastapi import APIRouter

from app.routes.inference import base_inference_router
from app.routes.patient import base_patient_router
from app.routes.vital import base_vital_router

api_router = APIRouter(prefix="/api")
api_router.include_router(router=base_patient_router)
api_router.include_router(router=base_vital_router)
api_router.include_router(router=base_inference_router)
