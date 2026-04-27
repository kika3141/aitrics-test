from fastapi import APIRouter

from app.routes.patient.patients import patients_router
from app.routes.patient.patients_vitals import patients_vitals_router

base_v1_patient_router = APIRouter(prefix="/v1")
base_v1_patient_router.include_router(router=patients_router, prefix="/patients")
base_v1_patient_router.include_router(
    router=patients_vitals_router, prefix="/patients/{patient_id}/vitals"
)

base_patient_router = APIRouter()
base_patient_router.include_router(router=base_v1_patient_router)
