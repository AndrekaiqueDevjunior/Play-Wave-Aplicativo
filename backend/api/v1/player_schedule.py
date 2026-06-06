"""
Endpoint principal do player para buscar programação resolvida.

GET /api/v1/player/schedule
  - Autenticado por device_token (header X-Device-Token ou query ?device_token=)
  - Retorna spots elegíveis, playlist ativa, versão e server_time
  - Todos os dados são validados por tenant_id

GET /api/v1/devices/{device_id}/debug-playback
  - Requer autenticação de admin/operator
  - Mostra programação completa com motivo de inclusão/exclusão de cada spot
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status as http_status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from core.models import (
    AudioPlaylist,
    AudioSpot,
    AudioSpotSchedule,
    AudioTrack,
    Campaign,
    Device,
    User,
)
from services.spot_resolver import (
    resolve_for_device,
    _is_schedule_active,
    _resolve_insertion_policy,
)

router = APIRouter(tags=["player"])
log = logging.getLogger("playwave.player_schedule")


# ─── Auth helpers ─────────────────────────────────────────────────────────────

def _get_device_by_token(
    db: Session,
    device_id: str,
    device_token: str,
) -> Device:
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Dispositivo não encontrado")
    if not device.device_token or device.device_token != device_token:
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, detail="Token inválido")
    if device.is_blocked:
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, detail="Dispositivo bloqueado")
    return device


# ─── GET /api/v1/player/schedule ─────────────────────────────────────────────

@router.get("/player/schedule")
def get_player_schedule(
    *,
    db: Session = Depends(get_db),
    device_id: str = Query(..., description="ID do dispositivo"),
    device_token: str = Query(..., description="Token do dispositivo"),
):
    """
    Retorna a programação resolvida para o player.

    O player deve chamar este endpoint quando receber notificação de mudança
    ou ao inicializar. Todos os dados retornados pertencem ao tenant do device.
    """
    device = _get_device_by_token(db, device_id, device_token)
    tenant_id = str(device.tenant_id) if device.tenant_id else None
    now = datetime.utcnow()

    if not tenant_id:
        raise HTTPException(
            http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dispositivo não possui tenant associado",
        )

    # ── Resolver campanha ativa ──────────────────────────────────────────────
    campaign = None
    campaign_id = None
    if device.current_campaign_id:
        campaign = db.query(Campaign).filter(Campaign.id == device.current_campaign_id).first()
        if campaign and campaign.tenant_id and str(campaign.tenant_id) != tenant_id:
            campaign = None  # cross-tenant: ignora silenciosamente
        if campaign:
            campaign_id = str(campaign.id)

    # ── Resolver playlist ────────────────────────────────────────────────────
    playlist = None
    playlist_id = None
    if campaign and campaign.audio_playlist_id:
        playlist = db.query(AudioPlaylist).filter(
            AudioPlaylist.id == campaign.audio_playlist_id
        ).first()
    elif device.audio_playlist_id:
        playlist = db.query(AudioPlaylist).filter(
            AudioPlaylist.id == device.audio_playlist_id
        ).first()

    if playlist:
        pl_status = playlist.status.value if hasattr(playlist.status, "value") else str(playlist.status)
        if pl_status != "active" or (playlist.tenant_id and str(playlist.tenant_id) != tenant_id):
            playlist = None
    if playlist:
        playlist_id = str(playlist.id)

    # ── Resolver spots elegíveis ─────────────────────────────────────────────
    spot_schedules = resolve_for_device(
        db,
        tenant_id=tenant_id,
        device_id=device_id,
        now=now,
        playlist_id=playlist_id,
        campaign_id=campaign_id,
    )

    # ── Montar resposta ──────────────────────────────────────────────────────
    response = {
        "device_id": device_id,
        "device_name": device.name,
        "server_time": now.isoformat(),
        "schedule_version": device.schedule_version,
        "tenant_id": tenant_id,
        "campaign": {
            "id": str(campaign.id),
            "name": campaign.name,
            "campaign_version": campaign.campaign_version,
        } if campaign else None,
        "audio_playlist": _build_playlist_payload(db, playlist) if playlist else None,
        "spot_schedules": spot_schedules,
    }

    log.info(
        "player.schedule.resolved",
        extra={
            "tenant_id": tenant_id,
            "device_id": device_id,
            "schedule_version": device.schedule_version,
            "spots_eligible": len(spot_schedules),
        },
    )

    return response


def _build_playlist_payload(db: Session, playlist: AudioPlaylist) -> dict:
    from api.v1.devices import _audio_playlist_track_payload, _build_folder_schedules_payload
    return {
        "id": str(playlist.id),
        "name": playlist.name,
        "volume": playlist.volume_default,
        "loop": playlist.loop_enabled,
        "shuffle": playlist.shuffle_enabled,
        "version": playlist.version,
        "tracks": _audio_playlist_track_payload(db, playlist=playlist),
        "folder_schedules": _build_folder_schedules_payload(db, playlist_id=playlist.id),
    }


# ─── GET /api/v1/devices/{device_id}/debug-playback ──────────────────────────

@router.get("/devices/{device_id}/debug-playback")
def debug_device_playback(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
):
    """
    Diagnóstico de programação de um dispositivo.
    Mostra todos os spots com motivo de elegibilidade ou rejeição.
    Requer autenticação de usuário admin ou operator.
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Dispositivo não encontrado")

    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, detail="Sem permissão")

    now = datetime.utcnow()
    tenant_id = str(device.tenant_id) if device.tenant_id else None

    # Campanha
    campaign = None
    if device.current_campaign_id:
        campaign = db.query(Campaign).filter(Campaign.id == device.current_campaign_id).first()

    # Playlist
    playlist = None
    playlist_id = None
    if campaign and campaign.audio_playlist_id:
        playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == campaign.audio_playlist_id).first()
    elif device.audio_playlist_id:
        playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == device.audio_playlist_id).first()
    if playlist:
        playlist_id = str(playlist.id)

    # Todos os schedules visíveis pelo device
    from sqlalchemy import or_

    scope_filter = [AudioSpotSchedule.device_id == device.id]
    if playlist_id:
        scope_filter.append(AudioSpotSchedule.playlist_id == playlist_id)
    if campaign:
        scope_filter.append(AudioSpotSchedule.campaign_id == campaign.id)

    all_schedules = (
        db.query(AudioSpotSchedule)
        .filter(or_(*scope_filter))
        .order_by(AudioSpotSchedule.priority.desc())
        .all()
    )

    spots_detail = []
    for schedule in all_schedules:
        spot = db.query(AudioSpot).filter(AudioSpot.id == schedule.spot_id).first()
        track = db.query(AudioTrack).filter(AudioTrack.id == spot.track_id).first() if spot else None

        rejections = []

        if not schedule.is_active:
            rejections.append("schedule.is_active=False")
        if schedule.tenant_id and tenant_id and str(schedule.tenant_id) != tenant_id:
            rejections.append(f"cross_tenant: schedule.tenant={schedule.tenant_id}")
        if spot:
            spot_status = spot.status.value if hasattr(spot.status, "value") else str(spot.status)
            if spot_status != "active":
                rejections.append(f"spot.status={spot_status}")
            if spot.tenant_id and tenant_id and str(spot.tenant_id) != tenant_id:
                rejections.append(f"cross_tenant: spot.tenant={spot.tenant_id}")
        else:
            rejections.append("spot_not_found")

        if track:
            track_status = track.status.value if hasattr(track.status, "value") else str(track.status)
            if track_status != "active":
                rejections.append(f"track.status={track_status}")
        else:
            rejections.append("track_not_found")

        if schedule.starts_at and now < schedule.starts_at:
            rejections.append(f"antes_de_starts_at={schedule.starts_at.isoformat()}")
        if schedule.ends_at and now > schedule.ends_at:
            rejections.append(f"apos_ends_at={schedule.ends_at.isoformat()}")

        if schedule.days_of_week and now.weekday() not in schedule.days_of_week:
            rejections.append(f"dia_invalido: hoje={now.weekday()}, permitidos={schedule.days_of_week}")

        if schedule.start_time and schedule.end_time:
            from services.spot_resolver import _is_within_time_window
            if not _is_within_time_window(schedule, now):
                rejections.append(
                    f"fora_do_horario: {schedule.start_time}-{schedule.end_time}, agora={now.strftime('%H:%M')}"
                )

        eligible = len(rejections) == 0

        spots_detail.append({
            "schedule_id": str(schedule.id),
            "spot_id": str(schedule.spot_id),
            "spot_name": spot.name if spot else None,
            "track_file": track.file_url if track else None,
            "interval_seconds": schedule.interval_seconds,
            "start_time": schedule.start_time,
            "end_time": schedule.end_time,
            "starts_at": schedule.starts_at.isoformat() if schedule.starts_at else None,
            "ends_at": schedule.ends_at.isoformat() if schedule.ends_at else None,
            "days_of_week": schedule.days_of_week,
            "priority": schedule.priority,
            "is_active": schedule.is_active,
            "insertion_policy": _resolve_insertion_policy(schedule, spot) if spot else None,
            "scope": {
                "playlist_id": str(schedule.playlist_id) if schedule.playlist_id else None,
                "campaign_id": str(schedule.campaign_id) if schedule.campaign_id else None,
                "device_id": str(schedule.device_id) if schedule.device_id else None,
            },
            "eligible": eligible,
            "rejections": rejections,
        })

    device_status = device.status.value if hasattr(device.status, "value") else str(device.status)
    online = device_status == "online"

    pl_status = None
    if playlist:
        pl_status = playlist.status.value if hasattr(playlist.status, "value") else str(playlist.status)

    return {
        "device_id": device_id,
        "device_name": device.name,
        "device_status": device_status,
        "online": online,
        "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
        "schedule_version": device.schedule_version,
        "tenant_id": tenant_id,
        "server_time": now.isoformat(),
        "campaign": {
            "id": str(campaign.id),
            "name": campaign.name,
            "status": str(campaign.status.value if hasattr(campaign.status, "value") else campaign.status),
            "campaign_version": campaign.campaign_version,
            "audio_playlist_id": str(campaign.audio_playlist_id) if campaign.audio_playlist_id else None,
        } if campaign else None,
        "playlist": {
            "id": playlist_id,
            "name": playlist.name if playlist else None,
            "status": pl_status,
            "version": playlist.version if playlist else None,
        } if playlist else None,
        "spots_total": len(spots_detail),
        "spots_eligible": sum(1 for s in spots_detail if s["eligible"]),
        "spots_rejected": sum(1 for s in spots_detail if not s["eligible"]),
        "spots": spots_detail,
    }
