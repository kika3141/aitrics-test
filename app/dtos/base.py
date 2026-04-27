from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer, model_validator


class BaseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Naive UTC throughout — timezone 정보가 포함된 datetime 입력 시 자동 제거
    @model_validator(mode="after")
    def strip_timezone(self) -> "BaseDto":
        for name, field_info in self.__class__.model_fields.items():
            value = getattr(self, name)
            if isinstance(value, datetime) and value.tzinfo is not None:
                object.__setattr__(self, name, value.replace(tzinfo=None))
        return self

    @field_serializer("*")
    @classmethod
    def serialize_fields(cls, value: object) -> object:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None).isoformat() + "Z"
        if isinstance(value, UUID):
            return str(value)
        return value
