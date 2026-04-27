import logging
import traceback

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.error_code import ErrorCode, ServerErrorCode


class AitricsException(Exception):
    """커스텀 예외 베이스 클래스"""

    def __init__(
        self,
        message: str | None = None,
        err_code: ErrorCode = ServerErrorCode.SERVER_ERROR,
        status_code: int | None = None,
    ) -> None:
        self.message = message
        self.err_code = err_code
        self.status_code = status_code

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message} - {self.err_code.value} - {self.status_code}"


class NotFoundException(AitricsException):
    def __init__(
        self,
        message: str = "Resource not found",
        err_code: ErrorCode = ServerErrorCode.NOT_FOUND,
    ):
        super().__init__(message=message, err_code=err_code, status_code=404)


class ConflictException(AitricsException):
    def __init__(
        self,
        message: str = "Version conflict",
        err_code: ErrorCode = ServerErrorCode.CONFLICT,
    ):
        super().__init__(message=message, err_code=err_code, status_code=409)


class UnauthorizedException(AitricsException):
    def __init__(
        self,
        message: str = "Unauthorized",
        err_code: ErrorCode = ServerErrorCode.UNAUTHORIZED,
    ):
        super().__init__(message=message, err_code=err_code, status_code=401)


class ServerException(AitricsException):
    def __init__(
        self,
        message: str = "Internal server error",
        err_code: ErrorCode = ServerErrorCode.SERVER_ERROR,
    ):
        super().__init__(message=message, err_code=err_code, status_code=500)


# --- 응답 스키마 ---


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    err_code: str


# --- Global Exception Handlers ---


async def aitrics_exception_handler(request: Request, exc: AitricsException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code or 500,
        content=ErrorResponse(
            message=exc.message or "Internal server error",
            err_code=exc.err_code.value,
        ).model_dump(),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logging.error(f"Validation exception: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=ErrorResponse(
            message="Input validation failed.",
            err_code=ServerErrorCode.UNPROCESSABLE_ENTITY.value,
        ).model_dump(),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    logging.error(f"HTTP exception: {exc.status_code} {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.detail if exc.detail else "Internal server error",
            err_code=ServerErrorCode.SERVER_ERROR.value,
        ).model_dump(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logging.error(f"Unhandled exception: {exc}")
    logging.error(f"Error traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            message="Internal server error",
            err_code=ServerErrorCode.SERVER_ERROR.value,
        ).model_dump(),
    )
