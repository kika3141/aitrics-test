import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, StarletteHTTPException

from app.core.config import settings
from app.core.exceptions import (
    AitricsException,
    aitrics_exception_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.routes import api_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

app = FastAPI(
    title="AITRICS Vital Risk API",
    version="0.1.0",
    description="Hospital vital signs management and rule-based risk scoring API",
)

app.add_exception_handler(AitricsException, aitrics_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
