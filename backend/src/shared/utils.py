from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
