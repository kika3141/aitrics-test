from fastapi import APIRouter

from app.routes.inference.inference import inference_router

base_v1_inference_router = APIRouter(prefix="/v1")
base_v1_inference_router.include_router(router=inference_router, prefix="/inference")

base_inference_router = APIRouter()
base_inference_router.include_router(router=base_v1_inference_router)
