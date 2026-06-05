"""
Audio Spot Scheduler — Determina qual spot deve ser inserido e quando.

Spots são anúncios/jingles inseridos em intervalos regulares durante a programação.

Regras:
1. Confere agendamentos ativos (is_active=true).
2. Filtra por horário e período (similar a folder_schedules).
3. Calcula o próximo spot elegível baseado no intervalo_seconds.
4. Aplica insertion_policy para decidir como inserir (interrupt, wait, mix).

TASK 08: Logs estruturados para diagnosticar spots não tocando.
"""

from datetime import datetime, time as time_class, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from core.models import AudioSpotSchedule, AudioSpot, AudioPlaylist
from core.logging_config import log_spot_check, log_spot_eligible, log_spot_ineligible, log_spot_due


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


def get_eligible_spots(
    db: Session,
    *,
    playlist_id: str,
    now: Optional[datetime] = None,
) -> List[Tuple[AudioSpot, AudioSpotSchedule]]:
    """
    Lista todos os spots elegíveis para uma playlist agora, em ordem de prioridade.

    Args:
        db: Sessão do banco.
        playlist_id: ID da playlist.
        now: Horário de referência (padrão: agora).

    Returns:
        Lista de tuplas (AudioSpot, AudioSpotSchedule) em ordem de prioridade decrescente.
    """
    if now is None:
        now = datetime.utcnow()

    schedules = (
        db.query(AudioSpotSchedule)
        .filter(
            AudioSpotSchedule.playlist_id == playlist_id,
            AudioSpotSchedule.is_active.is_(True),
        )
        .order_by(AudioSpotSchedule.priority.desc())
        .all()
    )

    current_time = now.time()
    current_date = now.date()

    eligible = []

    # TASK 08: Log inicial de check
    log_spot_check(playlist_id, len(schedules), 0, now)

    for schedule in schedules:
        if not _schedule_matches_now(schedule, current_date, current_time):
            # TASK 08: Log de rejeição
            log_spot_ineligible(
                str(schedule.id),
                "schedule_time_mismatch",
                {
                    "start_time": schedule.start_time,
                    "end_time": schedule.end_time,
                    "current_time": current_time.isoformat(),
                    "starts_at": schedule.starts_at.isoformat() if schedule.starts_at else None,
                    "ends_at": schedule.ends_at.isoformat() if schedule.ends_at else None,
                },
            )
            continue

        spot = db.query(AudioSpot).filter(AudioSpot.id == schedule.spot_id).first()
        if not spot:
            log_spot_ineligible(str(schedule.id), "spot_not_found")
            continue

        # TASK 08: Log de spot elegível
        log_spot_eligible(
            str(spot.id),
            spot.name,
            str(schedule.id),
            schedule.interval_seconds,
            schedule.priority,
        )

        eligible.append((spot, schedule))

    return eligible


def get_next_spot_time(
    db: Session,
    *,
    playlist_id: str,
    current_track_started_at: Optional[datetime] = None,
    now: Optional[datetime] = None,
) -> Optional[Tuple[datetime, AudioSpot, AudioSpotSchedule]]:
    """
    Calcula QUANDO o próximo spot deve tocar.

    Baseado em `interval_seconds` do agendamento: se um track começou há 10 segundos
    e o intervalo é 30s, o spot toca em +20s.

    Args:
        db: Sessão do banco.
        playlist_id: ID da playlist.
        current_track_started_at: Quando a track atual começou (padrão: agora).
        now: Horário de referência (padrão: agora).

    Returns:
        Tupla (spot_time, AudioSpot, AudioSpotSchedule) ou None.
    """
    if now is None:
        now = datetime.utcnow()

    if current_track_started_at is None:
        current_track_started_at = now

    eligible_spots = get_eligible_spots(db, playlist_id=playlist_id, now=now)

    if not eligible_spots:
        return None

    next_spot = None
    next_time = None

    for spot, schedule in eligible_spots:
        interval = timedelta(seconds=schedule.interval_seconds)
        spot_time = current_track_started_at + interval

        if spot_time > now and (next_time is None or spot_time < next_time):
            next_time = spot_time
            next_spot = (spot_time, spot, schedule)

    # TASK 08: Log quando spot está due
    if next_spot:
        spot_time, spot, schedule = next_spot
        time_until = (spot_time - now).total_seconds()
        log_spot_due(str(spot.id), spot.name, schedule.interval_seconds, time_until)

    return next_spot


def should_retry_spot_with_fallback(
    db: Session,
    *,
    playlist_id: str,
    now: Optional[datetime] = None,
    attempt: int = 0,
) -> Optional[Tuple[AudioSpot, AudioSpotSchedule]]:
    """
    Retorna o próximo spot em fallback se o primeiro não conseguir tocar.

    Útil para tentar outro spot se o primeiro falhar (ex: track corrompida).

    Args:
        db: Sessão do banco.
        playlist_id: ID da playlist.
        now: Horário de referência.
        attempt: Qual tentativa (0=first, 1=second, etc).

    Returns:
        Tupla (AudioSpot, AudioSpotSchedule) ou None.
    """
    eligible = get_eligible_spots(db, playlist_id=playlist_id, now=now)

    if attempt < len(eligible):
        return eligible[attempt]

    return None


def _schedule_matches_now(
    schedule: AudioSpotSchedule,
    current_date,
    current_time: time_class,
) -> bool:
    """Verifica se um agendamento de spot se aplica agora."""

    if schedule.starts_at and current_date < schedule.starts_at.date():
        return False
    if schedule.ends_at and current_date > schedule.ends_at.date():
        return False

    if schedule.start_time and schedule.end_time:
        start_t = parse_time_str(schedule.start_time)
        end_t = parse_time_str(schedule.end_time)

        if not start_t or not end_t:
            return False

        if current_time < start_t or current_time >= end_t:
            return False

    return True
