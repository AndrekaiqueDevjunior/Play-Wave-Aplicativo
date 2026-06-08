"""
Audio Schedule Resolver — Determina qual pasta de áudio deve tocar em um horário específico.

Regras:
1. Confere agendamentos ativos (is_active=true).
2. Filtra por data (starts_at <= now <= ends_at, se configurado).
3. Filtra por horário (start_time <= now.time <= end_time, se configurado).
4. Filtra por dia da semana (se configurado).
5. Retorna pasta com maior prioridade se houver conflito.
"""

from datetime import datetime, time as time_class, date as date_class, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from core.models import AudioPlaylistFolderSchedule, AudioFolder, AudioPlaylist
from services.schedule_clock import (
    is_day_allowed,
    is_time_in_window,
    normalize_schedule_now,
    parse_hhmm,
    schedule_now,
)


def parse_time_str(time_str: Optional[str]) -> Optional[time_class]:
    """Converte string "HH:MM" para time object. Retorna None se inválido."""
    return parse_hhmm(time_str)


def get_current_day_of_week() -> int:
    """Retorna dia da semana: 0=seg, 1=ter, 2=qua, 3=qui, 4=sex, 5=sab, 6=dom"""
    return schedule_now().weekday()


def resolve_active_folder(
    db: Session,
    *,
    playlist_id: str,
    now: Optional[datetime] = None,
) -> Optional[AudioFolder]:
    """
    Resolve qual pasta deve estar tocando agora para uma playlist.

    Args:
        db: Sessão do banco.
        playlist_id: ID da playlist.
        now: Horário de referência (padrão: agora).

    Returns:
        AudioFolder elegível com maior prioridade, ou None se nenhuma elegível.
    """
    if now is None:
        now = schedule_now()
    else:
        now = normalize_schedule_now(now)

    schedules = (
        db.query(AudioPlaylistFolderSchedule)
        .filter(
            AudioPlaylistFolderSchedule.playlist_id == playlist_id,
            AudioPlaylistFolderSchedule.is_active.is_(True),
        )
        .order_by(AudioPlaylistFolderSchedule.priority.desc())
        .all()
    )

    current_time = now.time()
    current_date = now.date()
    current_dow = now.weekday()

    for schedule in schedules:
        if not _schedule_matches_now(
            schedule,
            current_date,
            current_time,
            current_dow,
        ):
            continue

        folder = db.query(AudioFolder).filter(AudioFolder.id == schedule.folder_id).first()
        if not folder or not folder.is_active:
            continue

        return folder

    return None


def resolve_active_folders_by_priority(
    db: Session,
    *,
    playlist_id: str,
    now: Optional[datetime] = None,
) -> List[AudioFolder]:
    """
    Resolve todas as pastas elegíveis em ordem de prioridade.

    Útil para fallbacks: tente a primeira, depois a segunda, etc.
    """
    if now is None:
        now = schedule_now()
    else:
        now = normalize_schedule_now(now)

    schedules = (
        db.query(AudioPlaylistFolderSchedule)
        .filter(
            AudioPlaylistFolderSchedule.playlist_id == playlist_id,
            AudioPlaylistFolderSchedule.is_active.is_(True),
        )
        .order_by(AudioPlaylistFolderSchedule.priority.desc())
        .all()
    )

    current_time = now.time()
    current_date = now.date()
    current_dow = now.weekday()

    folders = []
    seen_folder_ids = set()

    for schedule in schedules:
        if not _schedule_matches_now(
            schedule,
            current_date,
            current_time,
            current_dow,
        ):
            continue

        if schedule.folder_id in seen_folder_ids:
            continue

        folder = db.query(AudioFolder).filter(AudioFolder.id == schedule.folder_id).first()
        if not folder or not folder.is_active:
            continue

        folders.append(folder)
        seen_folder_ids.add(schedule.folder_id)

    return folders


def _schedule_matches_now(
    schedule: AudioPlaylistFolderSchedule,
    current_date: date_class,
    current_time: time_class,
    current_dow: int,
) -> bool:
    """Verifica se um agendamento se aplica agora."""

    if schedule.starts_at and current_date < schedule.starts_at.date():
        return False
    if schedule.ends_at and current_date > schedule.ends_at.date():
        return False

    if not is_time_in_window(current_time, schedule.start_time, schedule.end_time):
        return False

    if not is_day_allowed(schedule.days_of_week, current_dow):
        return False

    return True


def get_next_schedule_change(
    db: Session,
    *,
    playlist_id: str,
    now: Optional[datetime] = None,
) -> Optional[datetime]:
    """
    Calcula o próximo horário em que a pasta pode mudar.

    Útil para saber quando re-avaliar a playlist.
    """
    if now is None:
        now = schedule_now()
    else:
        now = normalize_schedule_now(now)

    schedules = (
        db.query(AudioPlaylistFolderSchedule)
        .filter(
            AudioPlaylistFolderSchedule.playlist_id == playlist_id,
            AudioPlaylistFolderSchedule.is_active.is_(True),
        )
        .all()
    )

    next_change = None

    for schedule in schedules:
        if _schedule_matches_now(schedule, now.date(), now.time(), now.weekday()):
            if schedule.end_time:
                end_t = parse_hhmm(schedule.end_time)
                if end_t:
                    candidate = now.replace(
                        hour=end_t.hour,
                        minute=end_t.minute,
                        second=0,
                        microsecond=0,
                    )
                    if candidate > now:
                        if next_change is None or candidate < next_change:
                            next_change = candidate

            if schedule.ends_at:
                next_midnight = schedule.ends_at.replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                next_midnight = (
                    next_midnight + timedelta(days=1)
                    if next_midnight <= now
                    else next_midnight
                )
                if next_change is None or next_midnight < next_change:
                    next_change = next_midnight

        else:
            if schedule.start_time:
                start_t = parse_hhmm(schedule.start_time)
                if start_t:
                    candidate = now.replace(
                        hour=start_t.hour,
                        minute=start_t.minute,
                        second=0,
                        microsecond=0,
                    )
                    if candidate > now:
                        if next_change is None or candidate < next_change:
                            next_change = candidate

            if schedule.starts_at:
                if schedule.starts_at > now:
                    if next_change is None or schedule.starts_at < next_change:
                        next_change = schedule.starts_at

    return next_change
