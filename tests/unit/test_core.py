"""core 모듈 유닛 테스트 — enums, auth, exceptions, utils"""

from datetime import UTC, datetime

import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.enums import BaseEnum
from app.core.exceptions import (
    AppException,
    ConflictException,
    NotFoundException,
    ServerException,
    UnauthorizedException,
    app_exception_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.utils import to_naive_utc, utcnow

# ── BaseEnum ─────────────────────────────────────────────────


class SampleEnum(BaseEnum):
    FOO = "FOO"
    BAR = "BAR"


def test_base_enum_case_insensitive_lookup():
    """소문자 입력 시 대문자 멤버로 매칭"""
    assert SampleEnum("foo") == SampleEnum.FOO
    assert SampleEnum("bar") == SampleEnum.BAR


def test_base_enum_mixed_case_lookup():
    """혼합 대소문자도 upper() 후 매칭"""
    assert SampleEnum("Foo") == SampleEnum.FOO


def test_base_enum_invalid_value():
    """존재하지 않는 값은 ValueError"""
    with pytest.raises(ValueError, match="Invalid SampleEnum"):
        SampleEnum("INVALID")


def test_base_enum_non_string_invalid():
    """문자열이 아닌 값은 ValueError"""
    with pytest.raises(ValueError, match="Invalid SampleEnum"):
        SampleEnum(999)


# ── Utils ────────��───────────────────────────────────────────


def test_utcnow_returns_naive():
    """utcnow()는 tzinfo 없는 datetime 반환"""
    now = utcnow()
    assert now.tzinfo is None


def test_to_naive_utc_with_tz():
    """tz-aware datetime → naive UTC 변환"""
    aware = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    naive = to_naive_utc(aware)
    assert naive.tzinfo is None
    assert naive == datetime(2025, 1, 1, 12, 0, 0)


def test_to_naive_utc_already_naive():
    """이미 naive datetime이면 그대로 반환"""
    naive = datetime(2025, 1, 1, 12, 0, 0)
    result = to_naive_utc(naive)
    assert result is naive


# ── Auth ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_token_success():
    """올바른 토큰이면 토큰 문자열 반환"""
    from app.core.auth import verify_token
    from app.core.config import settings

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=settings.api_token
    )
    result = await verify_token(credentials)
    assert result == settings.api_token


@pytest.mark.asyncio
async def test_verify_token_failure():
    """잘못된 토큰이면 UnauthorizedException"""
    from app.core.auth import verify_token

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="wrong-token"
    )
    with pytest.raises(UnauthorizedException):
        await verify_token(credentials)


# ── Exception Classes ──────���─────────────────────────────────


def test_not_found_exception_defaults():
    exc = NotFoundException()
    assert exc.status_code == 404
    assert exc.message == "Resource not found"


def test_conflict_exception_defaults():
    exc = ConflictException()
    assert exc.status_code == 409
    assert exc.message == "Version conflict"


def test_unauthorized_exception_defaults():
    exc = UnauthorizedException()
    assert exc.status_code == 401
    assert exc.message == "Unauthorized"


def test_server_exception_defaults():
    exc = ServerException()
    assert exc.status_code == 500
    assert exc.message == "Internal server error"


def test_app_exception_str():
    exc = NotFoundException(message="Patient not found")
    result = str(exc)
    assert "NotFoundException" in result
    assert "Patient not found" in result


# ── Exception Handlers ──────────���────────────────────────────


def _mock_request() -> Request:
    """테스트용 가짜 Request"""
    scope = {"type": "http", "method": "GET", "path": "/test"}
    return Request(scope)


@pytest.mark.asyncio
async def test_app_exception_handler():
    """AppException → JSON 응답 변환"""
    request = _mock_request()
    exc = NotFoundException(message="Patient not found")

    response = await app_exception_handler(request, exc)

    assert response.status_code == 404
    assert b"Patient not found" in response.body


@pytest.mark.asyncio
async def test_app_exception_handler_no_message():
    """message가 None이면 기본 메시지 사용"""
    request = _mock_request()
    exc = AppException(message=None, status_code=500)

    response = await app_exception_handler(request, exc)

    assert response.status_code == 500
    assert b"Internal server error" in response.body


@pytest.mark.asyncio
async def test_app_exception_handler_no_status():
    """status_code가 None이면 500 반환"""
    request = _mock_request()
    exc = AppException(message="error")

    response = await app_exception_handler(request, exc)

    assert response.status_code == 500


@pytest.mark.asyncio
async def test_validation_exception_handler():
    """RequestValidationError → 422 응답"""
    request = _mock_request()
    exc = RequestValidationError(errors=[{"msg": "field required"}])

    response = await validation_exception_handler(request, exc)

    assert response.status_code == 422
    assert b"Input validation failed" in response.body


@pytest.mark.asyncio
async def test_http_exception_handler():
    """StarletteHTTPException → 해당 status code 반환"""
    request = _mock_request()
    exc = StarletteHTTPException(status_code=403, detail="Forbidden")

    response = await http_exception_handler(request, exc)

    assert response.status_code == 403
    assert b"Forbidden" in response.body


@pytest.mark.asyncio
async def test_http_exception_handler_empty_detail():
    """detail이 빈 문자열이면 기본 메시지"""
    request = _mock_request()
    exc = StarletteHTTPException(status_code=500, detail="")

    response = await http_exception_handler(request, exc)

    assert response.status_code == 500
    assert b"Internal server error" in response.body


@pytest.mark.asyncio
async def test_general_exception_handler():
    """예상치 못한 Exception → 500"""
    request = _mock_request()
    exc = RuntimeError("unexpected error")

    response = await general_exception_handler(request, exc)

    assert response.status_code == 500
    assert b"Internal server error" in response.body
