"""
Media Period Validator — Valida se mídia está dentro do período configurado
TASK 17: Períodos em mídias (data, hora, dias da semana)
"""

from datetime import datetime, time as time_class
from typing import Optional
from core.models import Media
from services.schedule_clock import is_day_allowed, is_time_in_window, parse_hhmm, schedule_now


def parse_time_str(time_str: Optional[str]) -> Optional[time_class]:
    """Converte string "HH:MM" para time object."""
    return parse_hhmm(time_str)


def is_media_in_period(
    media: Media,
    now: Optional[datetime] = None,
) -> bool:
    """
    Verifica se mídia está dentro do período configurado.

    Retorna True se:
    - Data inicial passou (ou não definida)
    - Data final não passou (ou não definida)
    - Horário atual está dentro do range (ou não definido)
    - Dia da semana é permitido (ou não definido)

    Args:
        media: Objeto Media
        now: Horário de referência (padrão: agora)

    Returns:
        True se mídia deve ser exibida, False se deve ser ignorada
    """
    if now is None:
        now = schedule_now()

    current_date = now.date()
    current_time = now.time()
    current_dow = now.weekday()

    # Validar período de data
    if media.starts_at and current_date < media.starts_at.date():
        return False  # Ainda não começou

    if media.ends_at and current_date > media.ends_at.date():
        return False  # Já terminou

    # Validar período de horário
    if not is_time_in_window(current_time, media.start_time, media.end_time):
        return False

    # Validar dias da semana
    if not is_day_allowed(media.days_of_week, current_dow):
        return False

    return True


def get_media_availability_status(
    media: Media,
    now: Optional[datetime] = None,
) -> str:
    """
    Retorna status de disponibilidade da mídia.

    Returns:
        "vigente": Mídia está disponível agora
        "futura": Mídia vai estar disponível no futuro
        "expirada": Mídia já expirou
        "fora_horario": Mídia não está em horário ativo
    """
    if now is None:
        now = schedule_now()

    current_date = now.date()
    current_time = now.time()

    # Verificar data
    if media.starts_at and current_date < media.starts_at.date():
        return "futura"

    if media.ends_at and current_date > media.ends_at.date():
        return "expirada"

    # Verificar horário
    if not is_time_in_window(current_time, media.start_time, media.end_time):
        return "fora_horario"

    # Verificar dias da semana
    if not is_day_allowed(media.days_of_week, now.weekday()):
        return "fora_horario"

    return "vigente"
