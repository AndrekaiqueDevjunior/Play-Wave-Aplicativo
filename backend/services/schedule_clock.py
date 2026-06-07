from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from core.config import settings


def get_schedule_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(settings.APP_TIMEZONE)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def schedule_now() -> datetime:
    """Horario local usado para regras de programacao por data/hora."""
    return datetime.now(get_schedule_timezone()).replace(tzinfo=None)


def normalize_schedule_now(value: datetime) -> datetime:
    """Converte datetimes aware para o timezone operacional; naive ja e local."""
    if value.tzinfo is None:
        return value
    return value.astimezone(get_schedule_timezone()).replace(tzinfo=None)
