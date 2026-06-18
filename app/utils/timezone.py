from datetime import datetime
from zoneinfo import ZoneInfo


ECUADOR_TIMEZONE = ZoneInfo("America/Guayaquil")


def now_ecuador():
    return datetime.now(ECUADOR_TIMEZONE)


def now_ecuador_naive():
    return now_ecuador().replace(tzinfo=None)


def as_ecuador_naive(value):
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(ECUADOR_TIMEZONE).replace(tzinfo=None)
