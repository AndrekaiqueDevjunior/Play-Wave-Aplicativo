from datetime import datetime, time as time_class
from typing import Iterable, Optional
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


def parse_hhmm(value: Optional[str]) -> Optional[time_class]:
    """Converte HH:MM em time; retorna None para valor ausente/invalido."""
    if not value:
        return None
    try:
        hour, minute = str(value).split(":")[:2]
        return time_class(int(hour), int(minute))
    except (TypeError, ValueError):
        return None


def is_time_in_window(
    current_time: time_class,
    start_time: Optional[str],
    end_time: Optional[str],
) -> bool:
    """Valida janela HH:MM, incluindo janela parcial e cruzando meia-noite."""
    start = parse_hhmm(start_time)
    end = parse_hhmm(end_time)

    if start and end:
        if start <= end:
            return start <= current_time < end
        return current_time >= start or current_time < end
    if start:
        return current_time >= start
    if end:
        return current_time < end
    return True


_DAY_ALIASES = {
    "mon": 0,
    "monday": 0,
    "seg": 0,
    "segunda": 0,
    "tue": 1,
    "tuesday": 1,
    "ter": 1,
    "terca": 1,
    "wed": 2,
    "wednesday": 2,
    "qua": 2,
    "quarta": 2,
    "thu": 3,
    "thursday": 3,
    "qui": 3,
    "quinta": 3,
    "fri": 4,
    "friday": 4,
    "sex": 4,
    "sexta": 4,
    "sat": 5,
    "saturday": 5,
    "sab": 5,
    "sabado": 5,
    "sun": 6,
    "sunday": 6,
    "dom": 6,
    "domingo": 6,
}


def normalize_days_of_week(days: Optional[Iterable]) -> Optional[set[int]]:
    """Normaliza dias para Python weekday(): segunda=0 ... domingo=6."""
    if not days:
        return None

    normalized = set()
    for day in days:
        if isinstance(day, int):
            value = day
        else:
            text = str(day).strip().lower()
            value = int(text) if text.isdigit() else _DAY_ALIASES.get(text)
        if value is None or value < 0 or value > 6:
            return set()
        normalized.add(value)
    return normalized


def is_day_allowed(days: Optional[Iterable], weekday: int) -> bool:
    normalized = normalize_days_of_week(days)
    if normalized is None:
        return True
    return weekday in normalized
