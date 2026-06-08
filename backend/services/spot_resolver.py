"""SpotResolverService — determina quais spots estão elegíveis para tocar agora.

Filtros aplicados em ordem:
  1. tenant_id isolado
  2. Escopo (playlist / campaign / device)
  3. AudioSpot.status == active
  4. AudioSpotSchedule.is_active == True
  5. Período de validade (starts_at / ends_at)
  6. Dia da semana (days_of_week, 0=seg, 6=dom)
  7. Janela de horário (start_time / end_time) — suporta cruzar meia-noite
  8. interval_seconds > 0
  9. Ordena por prioridade DESC
"""

import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from services.schedule_clock import (
    is_day_allowed,
    is_time_in_window,
    normalize_schedule_now,
    schedule_now,
)
from core.models import (
    AudioSpot,
    AudioSpotSchedule,
    AudioTrack,
    AudioPlaybackEvent,
    AudioPlaybackEventType,
    AudioPlaybackResult,
)

log = logging.getLogger("playwave.spot_resolver")


# ─── Helpers de filtro ────────────────────────────────────────────────────────

def _is_within_date_range(schedule: AudioSpotSchedule, now: datetime) -> bool:
    if schedule.starts_at and now < schedule.starts_at:
        return False
    if schedule.ends_at and now > schedule.ends_at:
        return False
    return True


def _is_within_day_of_week(schedule: AudioSpotSchedule, now: datetime) -> bool:
    return is_day_allowed(schedule.days_of_week, now.weekday())


def _is_within_time_window(schedule: AudioSpotSchedule, now: datetime) -> bool:
    """Suporta janela cruzando meia-noite (ex: 22:00–06:00)."""
    t = now.time().replace(second=0, microsecond=0)
    return is_time_in_window(t, schedule.start_time, schedule.end_time)


def _is_schedule_active(schedule: AudioSpotSchedule, now: datetime) -> bool:
    return (
        schedule.is_active
        and _is_within_date_range(schedule, now)
        and _is_within_day_of_week(schedule, now)
        and _is_within_time_window(schedule, now)
    )


def _resolve_insertion_policy(schedule: AudioSpotSchedule, spot: AudioSpot) -> str:
    """Precedência: schedule.insertion_policy > spot.insertion_policy > wait_silence."""
    if schedule.insertion_policy:
        val = schedule.insertion_policy
        return val.value if hasattr(val, "value") else str(val)
    if spot.insertion_policy:
        val = spot.insertion_policy
        return val.value if hasattr(val, "value") else str(val)
    return "wait_silence"


def _to_player_payload(schedule: AudioSpotSchedule, spot: AudioSpot, track: AudioTrack) -> dict:
    return {
        "id": str(schedule.id),
        "spot_id": str(spot.id),
        "spot_name": spot.name,
        "track_id": str(track.id),
        "file_url": track.file_url,
        "duration_seconds": track.duration_seconds,
        "interval_seconds": schedule.interval_seconds,
        "starts_at": schedule.starts_at.isoformat() if schedule.starts_at else None,
        "ends_at": schedule.ends_at.isoformat() if schedule.ends_at else None,
        "days_of_week": schedule.days_of_week,
        "start_time": schedule.start_time,
        "end_time": schedule.end_time,
        "insertion_policy": _resolve_insertion_policy(schedule, spot),
        "priority": schedule.priority,
        "is_active": schedule.is_active,
    }


# ─── Resolver principal ───────────────────────────────────────────────────────

def resolve_for_device(
    db: Session,
    *,
    tenant_id: str,
    device_id: str,
    now: Optional[datetime] = None,
    playlist_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
) -> List[dict]:
    """
    Retorna lista de spot payloads elegíveis para tocar neste device agora.

    Args:
        tenant_id:    Tenant do device autenticado.
        device_id:    ID do device.
        now:          Momento de referência (default: utcnow).
        playlist_id:  Playlist ativa do device (via campaign ou direta).
        campaign_id:  Campanha ativa do device (se existir).
    """
    if now is None:
        now = schedule_now()
    else:
        now = normalize_schedule_now(now)

    # ── Buscar schedules candidatos ─────────────────────────────────────────
    from sqlalchemy import or_

    candidate_filters = [
        AudioSpotSchedule.tenant_id == tenant_id,
        AudioSpotSchedule.is_active.is_(True),
    ]

    scope_filter = []
    if playlist_id:
        scope_filter.append(AudioSpotSchedule.playlist_id == playlist_id)
    if campaign_id:
        scope_filter.append(AudioSpotSchedule.campaign_id == campaign_id)
    scope_filter.append(AudioSpotSchedule.device_id == device_id)

    if scope_filter:
        candidate_filters.append(or_(*scope_filter))

    schedules = (
        db.query(AudioSpotSchedule)
        .filter(*candidate_filters)
        .order_by(AudioSpotSchedule.priority.desc())
        .all()
    )

    results = []
    for schedule in schedules:
        # 1. Filtrar por data/dia/horário
        if not _is_schedule_active(schedule, now):
            log.debug(
                "spot_schedule.ignored",
                extra={
                    "schedule_id": str(schedule.id),
                    "reason": "fora_de_janela",
                    "now": now.isoformat(),
                },
            )
            continue

        # 2. Buscar spot e validar status
        spot = db.query(AudioSpot).filter(AudioSpot.id == schedule.spot_id).first()
        if not spot:
            continue

        spot_status = spot.status.value if hasattr(spot.status, "value") else str(spot.status)
        if spot_status != "active":
            log.debug(
                "spot_schedule.ignored",
                extra={
                    "schedule_id": str(schedule.id),
                    "spot_id": str(spot.id),
                    "reason": f"spot_status={spot_status}",
                },
            )
            continue

        # 3. Validar que spot é do mesmo tenant
        if spot.tenant_id and str(spot.tenant_id) != tenant_id:
            log.warning(
                "spot_schedule.ignored",
                extra={
                    "schedule_id": str(schedule.id),
                    "reason": "cross_tenant_spot",
                    "spot_tenant": str(spot.tenant_id),
                    "device_tenant": tenant_id,
                },
            )
            continue

        # 4. Buscar track
        track = db.query(AudioTrack).filter(
            AudioTrack.id == spot.track_id,
        ).first()
        if not track:
            continue

        track_status = track.status.value if hasattr(track.status, "value") else str(track.status)
        if track_status != "active":
            continue

        results.append(_to_player_payload(schedule, spot, track))

    log.info(
        "player.schedule.resolved",
        extra={
            "tenant_id": tenant_id,
            "device_id": device_id,
            "playlist_id": playlist_id,
            "campaign_id": campaign_id,
            "eligible_spots": len(results),
        },
    )

    return results
