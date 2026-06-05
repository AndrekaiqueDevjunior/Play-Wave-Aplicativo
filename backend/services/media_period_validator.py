"""
Media Period Validator — Valida se mídia está dentro do período configurado
TASK 17: Períodos em mídias (data, hora, dias da semana)
"""

from datetime import datetime, time as time_class
from typing import Optional
from core.models import Media


def parse_time_str(time_str: Optional[str]) -> Optional[time_class]:
    """Converte string "HH:MM" para time object."""
    if not time_str:
        return None
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            return None
        return time_class(int(parts[0]), int(parts[1]))
    except (ValueError, AttributeError, IndexError):
        return None


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
        now = datetime.utcnow()

    current_date = now.date()
    current_time = now.time()
    current_day = now.strftime("%a").lower()  # "mon", "tue", etc

    # Validar período de data
    if media.starts_at and current_date < media.starts_at.date():
        return False  # Ainda não começou

    if media.ends_at and current_date > media.ends_at.date():
        return False  # Já terminou

    # Validar período de horário
    if media.start_time or media.end_time:
        start_t = parse_time_str(media.start_time)
        end_t = parse_time_str(media.end_time)

        if start_t and end_t:
            # Ambos definidos
            if current_time < start_t or current_time >= end_t:
                return False
        elif start_t:
            # Só início
            if current_time < start_t:
                return False
        elif end_t:
            # Só fim
            if current_time >= end_t:
                return False

    # Validar dias da semana
    if media.days_of_week and len(media.days_of_week) > 0:
        # Converter formato: "Monday" → "mon"
        day_abbrev = current_day[:3].lower()

        # Aceita tanto formato curto quanto longo
        allowed_days = [
            d.lower()[:3] if len(d) > 3 else d.lower()
            for d in media.days_of_week
        ]

        if day_abbrev not in allowed_days:
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
        now = datetime.utcnow()

    current_date = now.date()
    current_time = now.time()

    # Verificar data
    if media.starts_at and current_date < media.starts_at.date():
        return "futura"

    if media.ends_at and current_date > media.ends_at.date():
        return "expirada"

    # Verificar horário
    if media.start_time or media.end_time:
        start_t = parse_time_str(media.start_time)
        end_t = parse_time_str(media.end_time)

        if start_t and current_time < start_t:
            return "futura"
        if end_t and current_time >= end_t:
            return "expirada"
        if start_t and end_t and (current_time < start_t or current_time >= end_t):
            return "fora_horario"

    # Verificar dias da semana
    if media.days_of_week and len(media.days_of_week) > 0:
        current_day = now.strftime("%a").lower()
        day_abbrev = current_day[:3].lower()
        allowed_days = [
            d.lower()[:3] if len(d) > 3 else d.lower()
            for d in media.days_of_week
        ]

        if day_abbrev not in allowed_days:
            return "fora_horario"

    return "vigente"
