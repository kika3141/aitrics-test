from enum import Enum


class BaseEnum(str, Enum):
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            upper_value = value.upper()
            if upper_value in cls.__members__:
                return cls.__members__[upper_value]
        raise ValueError(f"Invalid {cls.__name__}: {value}")


class Gender(BaseEnum):
    M = "M"
    F = "F"
