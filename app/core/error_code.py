from app.core.enums import BaseEnum


class ErrorCode(BaseEnum):
    pass


class ServerErrorCode(ErrorCode):
    SERVER_ERROR = "SERVER_ERROR"
    BAD_PARAMETER = "BAD_PARAMETER"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"
    UNAUTHORIZED = "UNAUTHORIZED"
    UNPROCESSABLE_ENTITY = "UNPROCESSABLE_ENTITY"
