from datetime import UTC, datetime


def utcnow() -> datetime:
    """현재 UTC 시간을 naive datetime으로 반환"""
    return datetime.now(UTC).replace(tzinfo=None)


def to_naive_utc(dt: datetime) -> datetime:
    """tz-aware datetime을 naive UTC datetime으로 변환"""
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt
