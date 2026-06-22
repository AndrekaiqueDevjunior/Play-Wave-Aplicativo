import json
import secrets
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi import status as http_status
from pydantic import BaseModel, Field
import sqlalchemy as sa
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from core.dependencies import get_current_user
from core.models import (
    AudioFolder,
    AudioFolderTrack,
    AudioPlaylist,
    AudioPlaylistFolderSchedule,
    AudioPlaylistItem,
    AudioPlaylistStatus,
    AudioSpot,
    AudioSpotSchedule,
    AudioTrack,
    AudioTrackStatus,
    Campaign,
    CampaignPlaylistItem,
    DESTRUCTIVE_COMMAND_TYPES,
    Device,
    DeviceCommand,
    DeviceCommandStatus,
    DeviceEvent,
    DevicePairingCode,
    DevicePairingEventType,
    DeviceSession,
    Media,
    PlaybackLog,
    Tenant,
    User,
    ViewReport,
)
from core.schemas_completos import (
    DeviceCommandAck,
    DeviceCommandCreate,
    DeviceCommandResponse,
    DeviceCreate,
    DeviceDesktopExposureConfig,
    DeviceDesktopExposureConfigResponse,
    DeviceDesktopExposureConfigUpdate,
    DeviceOSDConfigUpdate,
    DevicePairingCodeCreate,
    DevicePairingEventResponse,
    DeviceResponse,
    DeviceSessionResponse,
    DeviceStatusEnum,
    DeviceUpdate,
    ForceRepairRequest,
    ForceRepairResponse,
    PairCodeStatusResponse,
    PairingEventActor,
    PairingEventListResponse,
    RegenerateCodeRequest,
    RegenerateCodeResponse,
)
from crud.entidades.crud_device_command import crud_device_command
from crud.entidades.crud_campaign import crud_campaign
from crud.entidades.crud_device import crud_device
from crud.entidades.crud_device_pairing_code import crud_device_pairing_code
from crud.entidades.crud_device_pairing_event import crud_device_pairing_event
from crud.entidades.crud_playback_log import crud_playback_log
from services.schedule_clock import schedule_now


# ─── Request body models ─────────────────────────────────────────────────────

class PairRequestBody(BaseModel):
    pairing_code: Optional[str] = None
    player_version: Optional[str] = None
    os: Optional[str] = None
    screen_resolution: Optional[str] = None


class HeartbeatBody(BaseModel):
    ip_address: Optional[str] = None
    player_version: Optional[str] = None
    storage_used: Optional[int] = None
    current_campaign_id: Optional[str] = None
    current_config_version: Optional[str] = None
    current_media_id: Optional[str] = None
    current_media_name: Optional[str] = None
    current_audio_track_id: Optional[str] = None
    current_audio_track_name: Optional[str] = Field(None, max_length=500)
    current_audio_track_started_at: Optional[datetime] = None
    last_error: Optional[str] = None
    playback_status: Optional[str] = None


class PlaybackBody(BaseModel):
    campaign_id: Optional[str] = None
    media_id: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str = "completed"


# ─── Device-token dependency ─────────────────────────────────────────────────

class DeviceAuthError(HTTPException):
    """Erro de autenticacao de device com error_code padronizado.

    SPEC 004 — substitui HTTPException generica para que o player possa
    interpretar (`TOKEN_VERSION_MISMATCH`, `REQUIRES_REPAIRING`, etc.) e
    disparar forceRepair() automaticamente.
    """

    def __init__(
        self,
        error_code: str,
        detail: str,
        status_code: int = http_status.HTTP_401_UNAUTHORIZED,
        **extra,
    ):
        # Empacota error_code e extras dentro do `detail` (FastAPI serializa
        # como JSON do body de erro). Mantemos `detail` como string humana
        # tambem para clientes legados.
        payload = {"detail": detail, "error_code": error_code, **extra}
        super().__init__(status_code=status_code, detail=payload)
        self.error_code = error_code


def get_device_by_token(
    x_device_token: str = Header(..., alias="X-Device-Token"),
    x_device_token_version: Optional[str] = Header(None, alias="X-Device-Token-Version"),
    db: Session = Depends(get_db),
) -> Device:
    device = crud_device.get_by_device_token(db, device_token=x_device_token)
    if not device:
        raise DeviceAuthError(
            error_code="TOKEN_REVOKED",
            detail="Device token inválido ou revogado",
        )
    if device.is_blocked:
        raise DeviceAuthError(
            error_code="DEVICE_BLOCKED",
            detail="Dispositivo bloqueado",
            status_code=http_status.HTTP_403_FORBIDDEN,
        )
    if getattr(device, "requires_repairing", False):
        raise DeviceAuthError(
            error_code="REQUIRES_REPAIRING",
            detail="Dispositivo requer novo pareamento",
        )

    # SPEC 004 — validacao de token_version (defesa em profundidade).
    # Compat-period: header ausente eh aceito como versao do device (warn).
    current_version = getattr(device, "token_version", 1) or 1
    if x_device_token_version is None:
        # Compat: aceita silenciosamente. Em release futuro virar erro.
        print(
            f"[auth] WARN device {device.id}: sem header X-Device-Token-Version "
            f"(compat). Atual no banco: {current_version}"
        )
    else:
        try:
            received_version = int(x_device_token_version)
        except (TypeError, ValueError):
            raise DeviceAuthError(
                error_code="TOKEN_VERSION_REQUIRED",
                detail="Header X-Device-Token-Version inválido",
                current_version=current_version,
                received_version=x_device_token_version,
            )
        if received_version != current_version:
            raise DeviceAuthError(
                error_code="TOKEN_VERSION_MISMATCH",
                detail="Versão do token não confere — o pareamento foi atualizado",
                current_version=current_version,
                received_version=received_version,
            )

    return device


router = APIRouter(prefix="/devices", tags=["devices"])


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _clean_uuid_fields(data: dict) -> dict:
    """Convert empty strings to None for UUID-typed fields."""
    for field in ("audio_playlist_id", "current_campaign_id"):
        if data.get(field) == "":
            data[field] = None
    return data


def _invalidate_device_playlist_cache(device_id: Optional[str] = None) -> None:
    from core.config import get_redis_client

    redis_client = get_redis_client()
    if not redis_client:
        return
    try:
        if device_id:
            redis_client.delete(f"device_playlist:{device_id}")
            return
        for key in redis_client.scan_iter("device_playlist:*"):
            redis_client.delete(key)
    except Exception as exc:
        print(f"[devices] Redis cache invalidation error: {exc}")


def _publish_device_playlist_invalidated(device: Device, *, reason: str) -> None:
    try:
        from services.event_bus import publish_device_event

        publish_device_event(
            str(device.id),
            event_type="playlist_invalidated",
            campaign_id=str(device.current_campaign_id) if device.current_campaign_id else None,
            data={
                "config_version": device.config_version,
                "reason": reason,
            },
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[devices] broadcast playlist_invalidated failed for {device.id}: {exc}")


OSD_DEVICE_FIELDS = {
    "show_current_audio": "osd_show_current_audio",
    "position": "osd_position",
    "duration_seconds": "osd_duration_seconds",
    "opacity": "osd_opacity",
    "font_size": "osd_font_size",
}


def _enum_value(value):
    return value.value if hasattr(value, "value") else value


def _sync_campaigns_for_device(db: Session, *, device: Device, campaign_id: Optional[str]) -> None:
    device_id = str(device.id)
    target_campaign = None
    if campaign_id:
        target_campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not target_campaign:
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Campanha não encontrada",
            )
        if device.tenant_id and target_campaign.tenant_id and str(target_campaign.tenant_id) != str(device.tenant_id):
            raise HTTPException(
                status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Campanha não pertence ao tenant do dispositivo",
            )

    campaigns = db.query(Campaign).filter(Campaign.device_ids.isnot(None)).all()
    for campaign in campaigns:
        original_ids = [str(item) for item in (campaign.device_ids or [])]
        filtered_ids = [item for item in original_ids if item != device_id]
        if target_campaign and str(campaign.id) == str(target_campaign.id):
            filtered_ids.append(device_id)
        if filtered_ids != original_ids:
            campaign.device_ids = filtered_ids
            db.add(campaign)

    if target_campaign and not target_campaign.device_ids:
        target_campaign.device_ids = [device_id]
        db.add(target_campaign)

    device.current_campaign_id = target_campaign.id if target_campaign else None
    device.current_campaign = target_campaign.name if target_campaign else None
    db.add(device)


def _remove_device_from_campaigns(db: Session, *, device_id: str) -> None:
    campaigns = db.query(Campaign).filter(Campaign.device_ids.isnot(None)).all()
    changed = False

    for campaign in campaigns:
        original_ids = [str(item) for item in (campaign.device_ids or [])]
        next_ids = [item for item in original_ids if item != device_id]
        if next_ids != original_ids:
            campaign.device_ids = next_ids
            campaign.config_version = str(uuid.uuid4())
            db.add(campaign)
            changed = True

    if changed:
        db.commit()


def _playlist_cache_key(device_id: str) -> str:
    return f"device_playlist:{device_id}"


def _get_redis_client():
    from core.config import get_redis_client

    return get_redis_client()


def _campaign_payload(campaign: Campaign, *, device=None, tenant=None) -> dict:
    from services.audio_policy_resolver import resolve_campaign_audio_payload
    audio_info = resolve_campaign_audio_payload(campaign, device, tenant)
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "media_ids": campaign.media_ids or [],
        "media_order": campaign.media_order or [],
        "video_muted": campaign.video_muted is not False,
        "schedule_all_day": campaign.schedule_all_day,
        "schedule_days": campaign.schedule_days,
        "schedule_start_time": str(campaign.schedule_start_time) if campaign.schedule_start_time else None,
        "schedule_end_time": str(campaign.schedule_end_time) if campaign.schedule_end_time else None,
        "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
        "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
        "loop_count": campaign.loop_count,
        "config_version": campaign.config_version,
        # SPEC 005
        "audio_policy_default": audio_info["audio_policy_default"],
        "audio_fade_ms": audio_info["audio_fade_ms"],
    }


def _media_playback_duration(
    media: Media,
    *,
    item_override: Optional[int] = None,
) -> Optional[int]:
    media_type = media.type.value if hasattr(media.type, "value") else media.type
    if item_override and item_override > 0:
        return item_override
    if media.display_duration_seconds and media.display_duration_seconds > 0:
        return media.display_duration_seconds
    if media_type in ("image", "external_url"):
        return media.duration or 15
    return None


def _media_is_valid_for_player(media: Media, *, now: Optional[datetime] = None) -> bool:
    status_value = media.status.value if hasattr(media.status, "value") else media.status
    if status_value != "available" or media.is_active is False:
        return False
    now = now or datetime.utcnow()
    if media.starts_at and media.starts_at > now:
        return False
    if media.ends_at and media.ends_at < now:
        return False

    # TASK 17: Validar período de mídia (data, hora, dias da semana)
    from services.media_period_validator import is_media_in_period
    if not is_media_in_period(media, now=now):
        return False

    return True


def _item_window_active(
    item: CampaignPlaylistItem, *, now: Optional[datetime] = None
) -> bool:
    if not item.is_active:
        return False
    now = now or datetime.utcnow()
    if item.starts_at and item.starts_at > now:
        return False
    if item.ends_at and item.ends_at < now:
        return False
    return True


def _resolve_playlist_entries(
    db: Session, *, campaign: Campaign
) -> List[tuple[Optional[CampaignPlaylistItem], str]]:
    """Resolve campaign playlist as ordered (item, media_id) tuples.

    Prefers relational campaign_playlist_items; falls back to legacy
    media_order/media_ids JSON for campaigns not yet backfilled or migrated.
    """
    items = (
        db.query(CampaignPlaylistItem)
        .filter(CampaignPlaylistItem.campaign_id == campaign.id)
        .order_by(CampaignPlaylistItem.order_index, CampaignPlaylistItem.created_at)
        .all()
    )
    if items:
        return [(item, str(item.media_id)) for item in items]

    legacy_order = campaign.media_order or []
    legacy_ids = [
        item.get("media_id") if isinstance(item, dict) else item
        for item in legacy_order
    ] or (campaign.media_ids or [])
    return [(None, str(mid)) for mid in legacy_ids if mid]


def _build_media_payload(
    db: Session,
    *,
    campaign: Campaign,
    device=None,
    tenant=None,
) -> List[dict]:
    entries = _resolve_playlist_entries(db, campaign=campaign)
    if not entries:
        return []

    media_ids = {media_id for _, media_id in entries}
    media_items = db.query(Media).filter(Media.id.in_(media_ids)).all()
    media_by_id = {str(media.id): media for media in media_items}

    payload: List[dict] = []
    now = schedule_now()
    for item, media_id in entries:
        media = media_by_id.get(media_id)
        if not media or not _media_is_valid_for_player(media, now=now):
            continue
        if item is not None and not _item_window_active(item, now=now):
            continue

        media_type = media.type.value if hasattr(media.type, "value") else media.type
        item_duration = item.display_duration_seconds if item else None
        effective_duration = _media_playback_duration(media, item_override=item_duration)
        play_until_end = media_type in ("video", "audio") and not effective_duration

        starts_at = (item.starts_at if item and item.starts_at else media.starts_at)
        ends_at = (item.ends_at if item and item.ends_at else media.ends_at)

        # SPEC 005 — política de áudio efetiva por mídia
        from services.audio_policy_resolver import resolve_media_payload as _rmp
        audio_fields = _rmp(media, campaign, device, tenant)

        media_entry = {
            "id": str(media.id),
            "media_id": str(media.id),
            "name": media.name,
            "type": media_type,
            "file_url": media.file_url,
            "thumbnail_url": media.thumbnail_url,
            "duration": effective_duration,
            "duration_seconds": media.duration_seconds,
            "display_duration_seconds": effective_duration,
            "play_until_end": play_until_end,
            "file_version": media.file_version or 1,
            "file_hash": media.file_hash,
            "mime_type": media.mime_type,
            "status": media.status.value if hasattr(media.status, "value") else media.status,
            "starts_at": starts_at.isoformat() if starts_at else None,
            "ends_at": ends_at.isoformat() if ends_at else None,
            # SPEC 005
            "audio_policy_effective": audio_fields["audio_policy_effective"],
            "has_audio": audio_fields["has_audio"],
        }
        if item is not None:
            media_entry["item_id"] = str(item.id)
            media_entry["repeat_count"] = item.repeat_count or 1
            repeat = item.repeat_count or 1
        else:
            repeat = 1

        for _ in range(max(repeat, 1)):
            payload.append(media_entry)

    return payload


def _resolve_audio_playlist_entries(
    db: Session, *, playlist: AudioPlaylist
) -> List[tuple[Optional[AudioPlaylistItem], str]]:
    items = (
        db.query(AudioPlaylistItem)
        .filter(AudioPlaylistItem.playlist_id == playlist.id)
        .order_by(AudioPlaylistItem.order_index, AudioPlaylistItem.created_at)
        .all()
    )
    if items:
        return [(item, str(item.track_id)) for item in items if item.is_active]
    return [(None, str(track_id)) for track_id in (playlist.track_ids or []) if track_id]


def _audio_playlist_track_payload(
    db: Session, *, playlist: AudioPlaylist
) -> List[dict]:
    entries = _resolve_audio_playlist_entries(db, playlist=playlist)
    if not entries:
        return []
    track_ids = {track_id for _, track_id in entries}
    tracks = db.query(AudioTrack).filter(
        AudioTrack.id.in_(track_ids),
        sa.cast(AudioTrack.status, sa.Text) == "active",
    ).all()
    track_map = {str(t.id): t for t in tracks}
    ordered = []
    for item, track_id in entries:
        track = track_map.get(track_id)
        if not track:
            continue
        volume = (
            item.volume_override
            if item is not None and item.volume_override is not None
            else (playlist.track_volumes or {}).get(str(track.id), playlist.volume_default)
        )
        ordered.append({
            "id": str(track.id),
            "name": track.name,
            "file_url": track.file_url,
            "duration_seconds": track.duration_seconds or 0,
            "volume": volume,
        })
    return ordered


def _build_folder_schedules_payload(db: Session, *, playlist_id) -> List[dict]:
    schedules = (
        db.query(AudioPlaylistFolderSchedule)
        .filter(
            AudioPlaylistFolderSchedule.playlist_id == playlist_id,
            AudioPlaylistFolderSchedule.is_active.is_(True),
        )
        .order_by(AudioPlaylistFolderSchedule.priority.desc(), AudioPlaylistFolderSchedule.start_time)
        .all()
    )
    result = []
    for sched in schedules:
        folder: Optional[AudioFolder] = db.query(AudioFolder).filter(AudioFolder.id == sched.folder_id).first()
        if not folder:
            continue
        folder_tracks_raw = (
            db.query(AudioFolderTrack)
            .filter(AudioFolderTrack.folder_id == sched.folder_id)
            .order_by(AudioFolderTrack.order_index)
            .all()
        )
        track_ids = [str(ft.track_id) for ft in folder_tracks_raw]
        tracks = []
        if track_ids:
            track_objs = {
                str(t.id): t
                for t in db.query(AudioTrack).filter(
                    AudioTrack.id.in_(track_ids),
                    sa.cast(AudioTrack.status, sa.Text) == "active",
                ).all()
            }
            for tid in track_ids:
                t = track_objs.get(tid)
                if t:
                    tracks.append({
                        "id": str(t.id),
                        "name": t.name,
                        "file_url": t.file_url,
                        "duration_seconds": t.duration_seconds or 0,
                    })
        result.append({
            "id": str(sched.id),
            "folder_id": str(sched.folder_id),
            "folder_name": folder.name,
            "start_time": sched.start_time,
            "end_time": sched.end_time,
            "starts_at": sched.starts_at.isoformat() if sched.starts_at else None,
            "ends_at": sched.ends_at.isoformat() if sched.ends_at else None,
            "days_of_week": sched.days_of_week,
            "priority": sched.priority,
            "play_mode": sched.play_mode.value if sched.play_mode else "sequential",
            "tracks": tracks,
        })
    return result


def _build_spot_schedules_payload(
    db: Session,
    *,
    playlist_id=None,
    device: Optional[Device] = None,
    campaign: Optional[Campaign] = None,
) -> List[dict]:
    if device and device.tenant_id:
        from services.spot_resolver import resolve_for_device

        return resolve_for_device(
            db,
            tenant_id=str(device.tenant_id),
            device_id=str(device.id),
            playlist_id=str(playlist_id) if playlist_id else None,
            campaign_id=str(campaign.id) if campaign else None,
        )

    schedules = (
        db.query(AudioSpotSchedule)
        .filter(
            AudioSpotSchedule.playlist_id == playlist_id,
            AudioSpotSchedule.is_active.is_(True),
        )
        .order_by(AudioSpotSchedule.priority.desc())
        .all()
    )
    result = []
    for sched in schedules:
        spot: Optional[AudioSpot] = db.query(AudioSpot).filter(AudioSpot.id == sched.spot_id).first()
        if not spot:
            continue
        track: Optional[AudioTrack] = db.query(AudioTrack).filter(
            AudioTrack.id == spot.track_id,
            sa.cast(AudioTrack.status, sa.Text) == "active",
        ).first()
        if not track:
            continue
        result.append({
            "id": str(sched.id),
            "spot_id": str(sched.spot_id),
            "spot_name": spot.name,
            "interval_seconds": sched.interval_seconds,
            "start_time": sched.start_time,
            "end_time": sched.end_time,
            "starts_at": sched.starts_at.isoformat() if sched.starts_at else None,
            "ends_at": sched.ends_at.isoformat() if sched.ends_at else None,
            "days_of_week": sched.days_of_week,
            "priority": sched.priority,
            "insertion_policy": (
                sched.insertion_policy.value if sched.insertion_policy
                else spot.insertion_policy.value if spot.insertion_policy
                else "interrupt"
            ),
            "file_url": track.file_url,
        })
    return result


def _build_audio_playlist_from_model(
    playlist: AudioPlaylist,
    db: Session,
    *,
    device: Optional[Device] = None,
    campaign: Optional[Campaign] = None,
) -> Optional[dict]:
    tracks = _audio_playlist_track_payload(db, playlist=playlist)
    folder_schedules = _build_folder_schedules_payload(db, playlist_id=playlist.id)
    spot_schedules = _build_spot_schedules_payload(
        db,
        playlist_id=playlist.id,
        device=device,
        campaign=campaign,
    )
    return {
        "id": str(playlist.id),
        "name": playlist.name,
        "volume": playlist.volume_default,
        "loop": playlist.loop_enabled,
        "shuffle": playlist.shuffle_enabled,
        "tracks": tracks,
        "folder_schedules": folder_schedules,
        "spot_schedules": spot_schedules,
    }


def _build_audio_playlist(device: Device, db: Session) -> Optional[dict]:
    if not device.audio_playlist_id:
        return None
    playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == device.audio_playlist_id).first()
    if not playlist:
        return None
    status_val = playlist.status.value if hasattr(playlist.status, "value") else str(playlist.status)
    if not playlist or status_val != "active":
        return None
    return _build_audio_playlist_from_model(playlist, db, device=device)


def _resolve_player_campaign(db: Session, *, device: Device) -> Optional[Campaign]:
    if device.current_campaign_id:
        campaign = crud_campaign.get(db, id=str(device.current_campaign_id))
        if campaign:
            return campaign
    return crud_campaign.get_active_for_device(db, device_id=str(device.id))


def _build_player_playlist_response(db: Session, *, device: Device) -> dict:
    from services.osd_config_resolver import resolve_osd_config

    campaign = _resolve_player_campaign(db, device=device)
    tenant = db.query(Tenant).filter(Tenant.id == device.tenant_id).first() if device.tenant_id else None
    osd_config = resolve_osd_config(device, tenant)

    if not campaign:
        return {
            "device_name": device.name,
            "osd_config": osd_config,
            "campaign": None,
            "media": [],
            "audio_playlist": _build_audio_playlist(device, db),
            "desktop_exposure_config": device.desktop_exposure_config,
        }

    audio_playlist = None
    if campaign.audio_playlist_id:
        playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == campaign.audio_playlist_id).first()
        _ps = playlist.status.value if playlist and hasattr(playlist.status, "value") else (
            str(playlist.status) if playlist else None
        )
        if playlist and _ps == "active":
            audio_playlist = _build_audio_playlist_from_model(
                playlist,
                db,
                device=device,
                campaign=campaign,
            )
    elif device.audio_playlist_id:
        audio_playlist = _build_audio_playlist(device, db)

    campaign_spots = _build_spot_schedules_payload(
        db,
        playlist_id=str(audio_playlist["id"]) if audio_playlist else None,
        device=device,
        campaign=campaign,
    )
    if audio_playlist:
        audio_playlist["spot_schedules"] = campaign_spots
    elif campaign_spots:
        audio_playlist = {
            "id": None,
            "name": "Spots da campanha",
            "volume": device.audio_volume,
            "loop": False,
            "shuffle": False,
            "tracks": [],
            "folder_schedules": [],
            "spot_schedules": campaign_spots,
        }

    return {
        "device_name": device.name,
        "osd_config": osd_config,
        "campaign": _campaign_payload(campaign, device=device, tenant=tenant),
        "media": _build_media_payload(db, campaign=campaign, device=device, tenant=tenant),
        "audio_playlist": audio_playlist,
        "desktop_exposure_config": device.desktop_exposure_config,
    }


# ─── CRUD endpoints ───────────────────────────────────────────────────────────

@router.get("/", response_model=List[DeviceResponse])
def get_devices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    device_status: Optional[DeviceStatusEnum] = Query(None, alias="status"),
    device_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None),
):
    # Non-admin users are always restricted to their own tenant
    if current_user.role != "admin":
        tenant_id = str(current_user.tenant_id)

    if device_status:
        devices = crud_device.get_by_status(db, status=device_status)
    elif device_type:
        devices = crud_device.get_by_type(db, device_type=device_type)
    elif location:
        devices = crud_device.get_by_location(db, location=location)
    elif group:
        devices = crud_device.get_by_group(db, group=group)
    elif tenant_id:
        devices = crud_device.get_by_tenant(db, tenant_id=tenant_id)
    elif search:
        devices = crud_device.search(db, query=search, skip=skip, limit=limit)
    else:
        devices = crud_device.get_multi(db, skip=skip, limit=limit)

    # Second-pass tenant filter so no filter path leaks cross-tenant data
    if current_user.role != "admin":
        tid = str(current_user.tenant_id)
        devices = [d for d in devices if str(d.tenant_id) == tid]

    return devices


@router.get("/statistics/overview")
def get_device_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tenant_id = None if current_user.role == "admin" else str(current_user.tenant_id)
    return crud_device.get_statistics(db, tenant_id=tenant_id)


@router.get("/online/list", response_model=List[DeviceResponse])
def get_online_devices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    devices = crud_device.get_online(db)
    if current_user.role != "admin":
        tid = str(current_user.tenant_id)
        devices = [d for d in devices if str(d.tenant_id) == tid]
    return devices[skip: skip + limit]


@router.get("/offline/list", response_model=List[DeviceResponse])
def get_offline_devices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    devices = crud_device.get_offline(db)
    if current_user.role != "admin":
        tid = str(current_user.tenant_id)
        devices = [d for d in devices if str(d.tenant_id) == tid]
    return devices[skip: skip + limit]


@router.get("/pairing/waiting", response_model=List[DeviceResponse])
def get_waiting_pairing_devices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    devices = crud_device.get_waiting_pairing(db)
    if current_user.role != "admin":
        tid = str(current_user.tenant_id)
        devices = [d for d in devices if str(d.tenant_id) == tid]
    return devices[skip: skip + limit]


@router.post("/pair-request")
def pair_request(body: PairRequestBody, db: Session = Depends(get_db)):
    code = body.pairing_code or ("TV-" + secrets.token_hex(2).upper())
    print(f"[pair-request] code={code} player_version={body.player_version}")

    # Reuse existing entry if not expired
    existing = crud_device_pairing_code.get_by_code(db, code=code)
    if existing:
        if existing.expires_at > datetime.utcnow() and existing.status in ("waiting", "paired"):
            return {"code": existing.code, "expires_at": existing.expires_at.isoformat(), "status": existing.status}
        # Renew expired/cancelled entry
        existing.expires_at = datetime.utcnow() + timedelta(minutes=30)
        existing.status = "waiting"
        existing.player_version = body.player_version
        existing.os = body.os
        db.commit()
        db.refresh(existing)
        return {"code": existing.code, "expires_at": existing.expires_at.isoformat(), "status": existing.status}

    obj_in = DevicePairingCodeCreate(
        code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
        player_version=body.player_version,
        os=body.os,
    )
    pairing = crud_device_pairing_code.create_code(db, obj_in=obj_in)
    return {
        "code": pairing.code,
        "expires_at": pairing.expires_at.isoformat(),
        "status": pairing.status,
    }


def _paired_response(device, *, status: str = "paired") -> dict:
    """Monta resposta de status=paired incluindo token_version e pairing_version
    (SPEC 004) — o player persiste essas versoes em PairingStorage.
    """
    return {
        "status": status,
        "device_id": str(device.id),
        "device_token": device.device_token,
        "token_version": device.token_version or 1,
        "pairing_version": device.pairing_version or 1,
        "device_name": device.name,
    }


def _log_paired_event(db: Session, device, *, is_repair: bool) -> None:
    """Registra evento `paired` (primeira vez) ou `re_paired` (apos forceRepair/regenerate)."""
    event_type = (
        DevicePairingEventType.RE_PAIRED.value
        if is_repair
        else DevicePairingEventType.PAIRED.value
    )
    try:
        crud_device_pairing_event.log(
            db,
            device=device,
            event_type=event_type,
            new_token_version=device.token_version,
            new_pairing_version=device.pairing_version,
            commit=False,
        )
    except Exception as exc:  # noqa: BLE001 — audit nunca bloqueia o pairing
        print(f"[pairing] audit log failed: {exc}")


@router.get("/by-code/{code}/status", response_model=PairCodeStatusResponse)
def check_pairing_status(code: str, db: Session = Depends(get_db)):
    pairing = crud_device_pairing_code.get_by_code(db, code=code)
    if pairing:
        device_for_code = crud_device.get_by_pairing_code(db, pairing_code=code)

        if pairing.expires_at and pairing.expires_at < datetime.utcnow():
            if device_for_code and device_for_code.device_token:
                return _paired_response(device_for_code)
            return {"status": "expired", "device_id": None, "device_token": None}

        if pairing.status == "waiting" and device_for_code and device_for_code.device_token:
            print(f"[pairing] auto-linking code={code} to device={device_for_code.id}")
            pairing.status = "paired"
            pairing.device_id = device_for_code.id
            pairing.used_at = datetime.utcnow()
            db.commit()
            return _paired_response(device_for_code)

        if pairing.status == "waiting" and device_for_code and not device_for_code.device_token:
            # Gera token novo. Se pairing_version > 1, eh re-pareamento (apos
            # forceRepair/regenerate); senao, primeiro pareamento.
            is_repair = (device_for_code.pairing_version or 1) > 1
            device_for_code.device_token = secrets.token_urlsafe(32)
            device_for_code.requires_repairing = False
            device_for_code.status = "online"
            device_for_code.paired_at = datetime.utcnow()
            pairing.status = "paired"
            pairing.device_id = device_for_code.id
            pairing.used_at = datetime.utcnow()
            _log_paired_event(db, device_for_code, is_repair=is_repair)
            db.commit()
            db.refresh(device_for_code)
            return _paired_response(device_for_code)

        if pairing.status == "paired" and pairing.device_id:
            device = crud_device.get(db, id=str(pairing.device_id))
            if device:
                return _paired_response(device)

        print(f"[pairing] code={code} status={pairing.status}")
        return {"status": pairing.status, "device_id": None, "device_token": None}

    # Fallback admin-first.
    device = crud_device.get_by_pairing_code(db, pairing_code=code)
    if not device:
        raise HTTPException(status_code=404, detail="Código não encontrado")

    if device.is_blocked:
        return {"status": "expired", "device_id": None, "device_token": None}

    if device.device_token:
        print(f"[pairing] code={code} fallback direct device match id={device.id}")
        return _paired_response(device)

    if device.status == "waiting_pairing":
        is_repair = (device.pairing_version or 1) > 1
        device.device_token = secrets.token_urlsafe(32)
        device.requires_repairing = False
        device.paired_at = datetime.utcnow()
        _log_paired_event(db, device, is_repair=is_repair)
        db.commit()
        db.refresh(device)
        return _paired_response(device)

    return {"status": "waiting", "device_id": None, "device_token": None}


@router.get("/{device_id}/playlist")
def get_device_playlist(
    device_id: str,
    device: Device = Depends(get_device_by_token),
    db: Session = Depends(get_db),
):
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Token não corresponde ao dispositivo")

    redis_client = _get_redis_client()
    cache_key = _playlist_cache_key(device_id)
    
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            print(f"[playlist] Redis error: {e}")

    response = jsonable_encoder(_build_player_playlist_response(db, device=device))

    _sync_device_config_version(db, device, response)

    if redis_client:
        try:
            redis_client.setex(cache_key, 30, json.dumps(response))
        except Exception as e:
            print(f"[playlist] Redis set error: {e}")

    return response


@router.get("/{device_id}/versions")
def get_device_player_versions(
    device_id: str,
    device: Device = Depends(get_device_by_token),
    db: Session = Depends(get_db),
):
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Token não corresponde ao dispositivo")

    campaign = _resolve_player_campaign(db, device=device)
    playlist = None
    if campaign and campaign.audio_playlist_id:
        playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == campaign.audio_playlist_id).first()
    elif device.audio_playlist_id:
        playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == device.audio_playlist_id).first()

    return jsonable_encoder({
        "device_id": str(device.id),
        "schedule_version": device.schedule_version or 0,
        "campaign_id": str(campaign.id) if campaign else None,
        "campaign_version": (campaign.campaign_version or 0) if campaign else 0,
        "config_version": campaign.config_version if campaign else None,
        "audio_playlist_id": str(playlist.id) if playlist else None,
        "audio_playlist_version": (playlist.version or 0) if playlist else 0,
        "updated_at": device.updated_at,
        "server_time": schedule_now(),
    })


@router.get("/{device_id}/debug-playback")
def debug_playback(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Debug de playback (TASK 34): diagnóstico real-time do que DEVERIA tocar.

    Mostra: campanha ativa, mídias válidas, mídias ignoradas (+ motivo),
    playlist sonora ativa, spots elegíveis, versões de sincronização.

    Acesso: admin ou operador do tenant do dispositivo.
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")

    now = schedule_now()
    campaign = _resolve_player_campaign(db, device=device)
    campaign_media = []
    campaign_media_ignored = []

    # TASK 35: Log quando campanha é carregada
    from core.event_logger import log_event, EventType, log_campaign_media_selected, log_campaign_media_ignored
    if campaign:
        log_event(
            EventType.CAMPAIGN_LOADED,
            device_id=str(device.id),
            details={"campaign_id": str(campaign.id), "campaign_name": campaign.name},
        )

    if campaign:
        entries = _resolve_playlist_entries(db, campaign=campaign)
        media_ids = {media_id for _, media_id in entries}
        media_items = db.query(Media).filter(Media.id.in_(media_ids)).all()
        media_by_id = {str(m.id): m for m in media_items}

        for item, media_id in entries:
            media = media_by_id.get(media_id)
            if not media:
                campaign_media_ignored.append({"media_id": media_id, "reason": "not_found"})
                continue
            if not _media_is_valid_for_player(media, now=now):
                # TASK 17: Diagnóstico de rejeição por período
                from services.media_period_validator import get_media_availability_status

                if media.status.value != "available":
                    reason = f"status_{media.status.value}"
                elif not media.is_active:
                    reason = "inactive"
                elif media.starts_at and media.starts_at > now:
                    reason = "not_started"
                elif media.ends_at and media.ends_at < now:
                    reason = "expired"
                else:
                    # Rejeição por período (hora, dia da semana)
                    reason = f"period_{get_media_availability_status(media, now=now)}"

                # TASK 35: Log mídia ignorada
                log_campaign_media_ignored(
                    str(device.id),
                    str(campaign.id),
                    str(media.id),
                    media.name,
                    reason,
                )
                campaign_media_ignored.append({"media_id": str(media.id), "media_name": media.name, "reason": reason})
                continue
            if item and not _item_window_active(item, now=now):
                if item.starts_at and item.starts_at > now:
                    reason = "item_not_started"
                elif item.ends_at and item.ends_at < now:
                    reason = "item_expired"
                else:
                    reason = "item_inactive"
                campaign_media_ignored.append({"media_id": str(media.id), "media_name": media.name, "reason": reason})
                continue
            # TASK 35: Log mídia selecionada
            log_campaign_media_selected(
                str(device.id),
                str(campaign.id),
                str(media.id),
                media.name,
            )
            campaign_media.append({
                "media_id": str(media.id),
                "media_name": media.name,
                "type": media.type.value if hasattr(media.type, "value") else media.type,
                "file_url": media.file_url[:80] if media.file_url else None,
            })

    audio_playlist_detail = None
    audio_folder_active = None
    audio_spots = []

    if campaign and campaign.audio_playlist_id:
        playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == campaign.audio_playlist_id).first()
    elif device.audio_playlist_id:
        playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == device.audio_playlist_id).first()
    else:
        playlist = None

    if playlist:
        from services.audio_schedule_resolver import resolve_active_folder
        from services.audio_spot_scheduler import get_eligible_spots

        active_folder = resolve_active_folder(db, playlist_id=str(playlist.id), now=now)
        audio_folder_active = {
            "folder_id": str(active_folder.id),
            "folder_name": active_folder.name,
        } if active_folder else None

        eligible = get_eligible_spots(db, playlist_id=str(playlist.id), now=now)
        audio_spots = [
            {
                "spot_id": str(s[0].id),
                "spot_name": s[0].name,
                "interval_seconds": s[1].interval_seconds,
                "priority": s[1].priority,
                "insertion_policy": s[0].insertion_policy.value if hasattr(s[0].insertion_policy, "value") else s[0].insertion_policy,
                "start_time": s[1].start_time,
                "end_time": s[1].end_time,
            }
            for s in eligible
        ]

        # TASK 08: Adicionar próximo spot due para diagnosticar
        next_spot_info = None
        if eligible:
            from services.audio_spot_scheduler import get_next_spot_time
            next_spot_result = get_next_spot_time(db, playlist_id=str(playlist.id), now=now)
            if next_spot_result:
                spot_time, spot, schedule = next_spot_result
                time_until = (spot_time - now).total_seconds()
                next_spot_info = {
                    "spot_id": str(spot.id),
                    "spot_name": spot.name,
                    "will_play_at": spot_time.isoformat(),
                    "seconds_until_play": time_until,
                    "interval_seconds": schedule.interval_seconds,
                }

        audio_playlist_detail = {
            "playlist_id": str(playlist.id),
            "playlist_name": playlist.name,
            "active_folder": audio_folder_active,
            "eligible_spots_count": len(audio_spots),
            "next_spot_due": next_spot_info,
        }

    return {
        "timestamp": now.isoformat(),
        "device": {
            "device_id": str(device.id),
            "device_name": device.name,
            "status": device.status.value if hasattr(device.status, "value") else device.status,
            "config_version": device.config_version,
        },
        "campaign": {
            "campaign_id": str(campaign.id) if campaign else None,
            "campaign_name": campaign.name if campaign else None,
            "config_version": campaign.config_version if campaign else None,
            "media_valid": campaign_media,
            "media_ignored": campaign_media_ignored,
        },
        "audio_playlist": audio_playlist_detail,
        "audio_spots": audio_spots,
        "info": "Se conteúdo não toca, procure em 'campaign.media_ignored' ou 'audio_playlist'",
    }


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
):
    device = (
        db.query(Device)
        .options(joinedload(Device.tenant))
        .filter(Device.id == device_id)
        .first()
    )
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado",
        )
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar este dispositivo",
        )
    response = DeviceResponse.model_validate(device)
    if current_user.role != "admin":
        response.device_token = None
    return response


def _validate_desktop_exposure_config(
    *,
    enabled: bool,
    interval_seconds: Optional[int],
    duration_seconds: Optional[int],
) -> None:
    if not enabled:
        return
    if interval_seconds is None or duration_seconds is None:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="desktop exposure requires interval_seconds and duration_seconds when enabled",
        )
    if duration_seconds >= interval_seconds:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="duration_seconds must be less than interval_seconds",
        )


@router.patch("/{device_id}/desktop-exposure-config", response_model=DeviceDesktopExposureConfigResponse)
def update_device_desktop_exposure_config(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
    body: DeviceDesktopExposureConfigUpdate,
):
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado",
        )
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar este dispositivo",
        )

    payload = body.model_dump(exclude_unset=True)
    if "enabled" in payload:
        device.desktop_exposure_enabled = payload["enabled"]
    if "interval_seconds" in payload:
        device.desktop_exposure_interval_seconds = payload["interval_seconds"]
    if "duration_seconds" in payload:
        device.desktop_exposure_duration_seconds = payload["duration_seconds"]
    if "restore_fullscreen" in payload:
        device.desktop_exposure_restore_fullscreen = payload["restore_fullscreen"]
    if "show_warning" in payload:
        device.desktop_exposure_show_warning = payload["show_warning"]
    if "warning_seconds_before" in payload:
        device.desktop_exposure_warning_seconds_before = payload["warning_seconds_before"]
    if "warning_text" in payload:
        device.desktop_exposure_warning_text = payload["warning_text"]
    if "warning_media_id" in payload:
        device.desktop_exposure_warning_media_id = payload["warning_media_id"] or None

    self_enabled = bool(device.desktop_exposure_enabled)
    _validate_desktop_exposure_config(
        enabled=self_enabled,
        interval_seconds=device.desktop_exposure_interval_seconds,
        duration_seconds=device.desktop_exposure_duration_seconds,
    )

    device.desktop_exposure_updated_at = datetime.utcnow()
    db.add(device)
    db.commit()
    db.refresh(device)

    _invalidate_device_playlist_cache(device_id=str(device.id))
    _publish_device_playlist_invalidated(device, reason="device_desktop_exposure_config_updated")

    return {
        "id": str(device.id),
        "desktop_exposure_config": device.desktop_exposure_config,
    }


@router.patch("/{device_id}/osd-config", response_model=DeviceResponse)
def update_device_osd_config(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
    body: DeviceOSDConfigUpdate,
):
    device = (
        db.query(Device)
        .options(joinedload(Device.tenant))
        .filter(Device.id == device_id)
        .first()
    )
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado",
        )
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar este dispositivo",
        )

    payload = body.model_dump(exclude_unset=True)
    for field, value in payload.items():
        setattr(device, OSD_DEVICE_FIELDS[field], _enum_value(value))
    db.add(device)
    db.commit()

    device = (
        db.query(Device)
        .options(joinedload(Device.tenant))
        .filter(Device.id == device_id)
        .first()
    )

    _invalidate_device_playlist_cache(device_id=str(device.id))
    _publish_device_playlist_invalidated(device, reason="device_osd_config_updated")
    response = DeviceResponse.model_validate(device)
    if current_user.role != "admin":
        response.device_token = None
    return response


@router.post("/", response_model=DeviceResponse, status_code=http_status.HTTP_201_CREATED)
def create_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_in: DeviceCreate,
):
    if crud_device.get_by_pairing_code(db, pairing_code=device_in.pairing_code):
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Código de pareamento já existe",
        )

    device_data = _clean_uuid_fields(device_in.model_dump())

    # Always assign tenant; non-admin cannot choose another tenant
    if current_user.role != "admin" or not device_data.get("tenant_id"):
        device_data["tenant_id"] = current_user.tenant_id

    device_data["device_token"] = secrets.token_urlsafe(32)

    try:
        db_obj = Device(**device_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        # Link matching DevicePairingCode if the player already registered this code
        crud_device_pairing_code.pair_with_device(
            db,
            pairing_code=db_obj.pairing_code,
            device_id=str(db_obj.id),
            tenant_id=str(db_obj.tenant_id),
        )

        return db_obj
    except IntegrityError as exc:
        db.rollback()
        err = str(exc.orig).lower()
        if "pairing_code" in err or "unique" in err:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="Código de pareamento já existe",
            )
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Conflito de dados únicos",
        )
    except DataError as exc:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Dado inválido: {exc.orig}",
        )
    except Exception as exc:
        db.rollback()
        print(f"[ERROR] create_device: {repr(exc)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar dispositivo",
        )


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
    device_in: DeviceUpdate,
):
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado",
        )
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar este dispositivo",
        )
    pairing_code_changed = bool(device_in.pairing_code and device_in.pairing_code != device.pairing_code)
    if pairing_code_changed:
        if crud_device.get_by_pairing_code(db, pairing_code=device_in.pairing_code):
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="Código de pareamento já existe",
            )

    update_data = _clean_uuid_fields(device_in.model_dump(exclude_unset=True))
    try:
        next_campaign_id = update_data.pop("current_campaign_id", None)
        for field, value in update_data.items():
            setattr(device, field, value)
        if pairing_code_changed:
            device.device_token = None
            device.requires_repairing = True
            device.pairing_version = (device.pairing_version or 1) + 1
            device.token_version = (device.token_version or 1) + 1
            device.status = "waiting_pairing"
            db.query(DeviceSession).filter(
                DeviceSession.device_id == device.id,
                DeviceSession.is_active == True,
            ).update(
                {
                    "is_active": False,
                    "revoked_at": datetime.utcnow(),
                },
                synchronize_session=False,
            )
        if "current_campaign_id" in device_in.model_fields_set:
            _sync_campaigns_for_device(db, device=device, campaign_id=next_campaign_id)
        db.commit()
        db.refresh(device)
        playlist_affecting_fields = (
            "current_campaign_id",
            "audio_playlist_id",
            "pairing_code",
            "audio_policy_default",
        )
        if any(field in device_in.model_fields_set for field in playlist_affecting_fields):
            _invalidate_device_playlist_cache(device_id=str(device.id))
        if "audio_policy_default" in device_in.model_fields_set:
            _publish_device_playlist_invalidated(device, reason="device_audio_policy_updated")
        # BUG D2 FIX: quando pairing_code muda, notifica o player via SSE para que
        # ele volte para tela de pareamento imediatamente (sem esperar próximo request 401).
        if pairing_code_changed:
            _publish_pairing_revoked(device.id, "code_changed")
        return device
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Conflito de dados únicos",
        )
    except DataError as exc:
        db.rollback()
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Dado inválido: {exc.orig}",
        )


@router.delete("/{device_id}")
def delete_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
):
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado",
        )
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para remover este dispositivo",
        )

    _remove_device_from_campaigns(db, device_id=device_id)

    db.query(PlaybackLog).filter(PlaybackLog.device_id == device_id).delete(synchronize_session=False)
    db.query(ViewReport).filter(ViewReport.device_id == device_id).delete(synchronize_session=False)
    db.query(DeviceEvent).filter(DeviceEvent.device_id == device_id).delete(synchronize_session=False)
    db.query(DeviceSession).filter(DeviceSession.device_id == device_id).delete(synchronize_session=False)
    db.query(DeviceCommand).filter(DeviceCommand.device_id == device_id).delete(synchronize_session=False)
    db.query(DevicePairingCode).filter(DevicePairingCode.device_id == device_id).update(
        {"device_id": None},
        synchronize_session=False,
    )
    crud_device.remove(db, id=device_id)
    return {"message": "Dispositivo removido com sucesso"}


@router.patch("/{device_id}/status")
def update_device_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
    device_status: DeviceStatusEnum,
):
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado",
        )
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar este dispositivo",
        )
    device = crud_device.update_status(db, db_obj=device, status=device_status)
    return {"message": f"Status atualizado para {device_status}"}


@router.post("/{device_id}/block")
def block_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
):
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado",
        )
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para bloquear este dispositivo",
        )
    device = crud_device.block_device(db, db_obj=device)
    # SPEC 004 — audit + SSE.
    crud_device_pairing_event.log(
        db,
        device=device,
        event_type=DevicePairingEventType.DEVICE_BLOCKED.value,
        requested_by_id=str(current_user.id),
    )
    _publish_pairing_revoked(device.id, "device_blocked")
    return {"message": "Dispositivo bloqueado com sucesso"}


@router.post("/{device_id}/unblock")
def unblock_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
):
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado",
        )
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para desbloquear este dispositivo",
        )
    device = crud_device.unblock_device(db, db_obj=device)
    crud_device_pairing_event.log(
        db,
        device=device,
        event_type=DevicePairingEventType.DEVICE_UNBLOCKED.value,
        requested_by_id=str(current_user.id),
    )
    return {"message": "Dispositivo desbloqueado com sucesso"}


def _revoke_device_sessions(db: Session, device_id: str) -> int:
    """Revoga sessoes ativas do device. Retorna quantas foram revogadas."""
    return db.query(DeviceSession).filter(
        DeviceSession.device_id == device_id,
        DeviceSession.is_active == True,
    ).update(
        {"is_active": False, "revoked_at": datetime.utcnow()},
        synchronize_session=False,
    )


def _publish_pairing_revoked(device_id: str, reason: str) -> None:
    """Notifica player via SSE que o pareamento foi revogado (SPEC 004).

    Player escuta `pairing:revoked` e dispara forceRepair() imediato em vez
    de esperar a proxima request 401.
    """
    try:
        from services.event_bus import publish_device_event

        publish_device_event(
            str(device_id),
            event_type="pairing:revoked",
            data={"reason": reason, "revoked_at": datetime.utcnow().isoformat()},
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[devices] pairing:revoked publish failed for {device_id}: {exc}")


@router.post(
    "/{device_id}/pairing-code/regenerate",
    response_model=RegenerateCodeResponse,
)
def regenerate_pairing_code(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
    body: Optional[RegenerateCodeRequest] = None,
):
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado",
        )
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar este dispositivo",
        )

    next_code = None
    for _ in range(10):
        candidate = "TV-" + secrets.token_hex(2).upper()
        if not crud_device.get_by_pairing_code(db, pairing_code=candidate):
            next_code = candidate
            break
    if not next_code:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível gerar código único de pareamento",
        )

    # Snapshot dos valores antigos para auditoria.
    old_code = device.pairing_code
    old_token_version = device.token_version or 1
    old_pairing_version = device.pairing_version or 1

    device.pairing_code = next_code
    device.device_token = None
    device.requires_repairing = True
    device.pairing_version = old_pairing_version + 1
    device.token_version = old_token_version + 1
    device.status = "waiting_pairing"

    revoked_count = _revoke_device_sessions(db, device.id)

    # SPEC 004 — registra evento de auditoria.
    crud_device_pairing_event.log(
        db,
        device=device,
        event_type=DevicePairingEventType.CODE_REGENERATED.value,
        requested_by_id=str(current_user.id),
        reason=(body.reason if body else None),
        previous_token_version=old_token_version,
        new_token_version=device.token_version,
        previous_pairing_version=old_pairing_version,
        new_pairing_version=device.pairing_version,
        previous_pairing_code=old_code,
        new_pairing_code=device.pairing_code,
        metadata={"revoked_sessions_count": revoked_count},
        commit=False,  # commit junto com o device abaixo
    )

    db.add(device)
    db.commit()
    db.refresh(device)
    _invalidate_device_playlist_cache(device_id=str(device.id))
    _publish_pairing_revoked(device.id, "code_regenerated")

    return RegenerateCodeResponse(
        pairing_code=device.pairing_code,
        pairing_version=device.pairing_version,
        token_version=device.token_version,
        revoked_sessions_count=revoked_count,
        previous_pairing_code=old_code,
    )


@router.post(
    "/{device_id}/force-repair",
    response_model=ForceRepairResponse,
)
def force_repair_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
    body: Optional[ForceRepairRequest] = None,
):
    """SPEC 004 — revoga tokens sem trocar o codigo de pareamento.

    Util quando o operador quer expulsar um player suspeito/clonado mas
    nao quer reconfigurar todas as TVs que usam o codigo atual.
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado",
        )
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para esta ação",
        )

    old_token_version = device.token_version or 1
    device.device_token = None
    device.token_version = old_token_version + 1
    device.requires_repairing = True
    # NAO mexe em pairing_code nem pairing_version.

    revoked_count = _revoke_device_sessions(db, device.id)

    crud_device_pairing_event.log(
        db,
        device=device,
        event_type=DevicePairingEventType.FORCE_REPAIR.value,
        requested_by_id=str(current_user.id),
        reason=(body.reason if body else None),
        previous_token_version=old_token_version,
        new_token_version=device.token_version,
        metadata={"revoked_sessions_count": revoked_count},
        commit=False,
    )

    db.add(device)
    db.commit()
    db.refresh(device)
    _invalidate_device_playlist_cache(device_id=str(device.id))
    _publish_pairing_revoked(device.id, "force_repair")

    return ForceRepairResponse(
        token_version=device.token_version,
        revoked_sessions_count=revoked_count,
        pairing_code_unchanged=device.pairing_code,
    )


@router.get(
    "/{device_id}/pairing-events",
    response_model=PairingEventListResponse,
)
def list_pairing_events(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
    limit: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = Query(None),
):
    """SPEC 004 — historico de eventos de pareamento de um device."""
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")

    events = crud_device_pairing_event.list_by_device(
        db, device_id=device_id, limit=limit, event_type=event_type
    )
    total = crud_device_pairing_event.count_by_device(
        db, device_id=device_id, event_type=event_type
    )

    # Resolve nome do usuario solicitante quando houver.
    items = []
    for ev in events:
        actor = None
        if ev.requested_by:
            user = db.query(User).filter(User.id == ev.requested_by).first()
            actor = PairingEventActor(
                id=str(ev.requested_by),
                name=(user.email if user else None),
            )
        items.append(
            DevicePairingEventResponse(
                id=str(ev.id),
                event_type=ev.event_type,
                previous_token_version=ev.previous_token_version,
                new_token_version=ev.new_token_version,
                previous_pairing_version=ev.previous_pairing_version,
                new_pairing_version=ev.new_pairing_version,
                previous_pairing_code=ev.previous_pairing_code,
                new_pairing_code=ev.new_pairing_code,
                requested_by=actor,
                reason=ev.reason,
                metadata=ev.extra_metadata,
                created_at=ev.created_at,
            )
        )

    return PairingEventListResponse(items=items, total=total)


@router.post("/{device_id}/heartbeat")
def device_heartbeat(
    device_id: str,
    body: HeartbeatBody,
    device: Device = Depends(get_device_by_token),
    db: Session = Depends(get_db),
):
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Token não corresponde ao dispositivo")

    device.last_seen_at = datetime.utcnow()
    if body.ip_address:
        device.ip_address = body.ip_address
    if body.player_version:
        device.player_version = body.player_version
    if body.storage_used is not None:
        device.storage_used = body.storage_used
    if body.current_config_version:
        device.config_version = body.current_config_version
    if body.current_campaign_id is not None:
        if body.current_campaign_id:
            campaign = db.query(Campaign).filter(Campaign.id == body.current_campaign_id).first()
            device.current_campaign_id = campaign.id if campaign else None
            device.current_campaign = campaign.name if campaign else None
        else:
            device.current_campaign_id = None
            device.current_campaign = None
    if "current_audio_track_id" in body.model_fields_set:
        if body.current_audio_track_id:
            try:
                device.current_audio_track_id = uuid.UUID(str(body.current_audio_track_id))
            except ValueError:
                raise HTTPException(
                    status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="current_audio_track_id inválido",
                )
            device.current_audio_track_name = body.current_audio_track_name
            device.current_audio_track_started_at = body.current_audio_track_started_at
        else:
            device.current_audio_track_id = None
            device.current_audio_track_name = None
            device.current_audio_track_started_at = None
    if device.status != "online":
        device.status = "online"
    db.add(device)
    db.commit()

    pending_count = db.query(DeviceCommand).filter(
        DeviceCommand.device_id == device_id,
        DeviceCommand.status == "pending",
    ).count()

    current_campaign = _resolve_player_campaign(db, device=device)
    target_version = current_campaign.config_version if current_campaign else None
    has_update = device.config_version != target_version

    return {
        "ok": True,
        "is_blocked": device.is_blocked,
        "config_version": device.config_version,
        "has_update": has_update,
        "playlist_updated": has_update,
        "pending_commands": pending_count,
        "server_time": datetime.utcnow().isoformat(),
    }


@router.post("/{device_id}/playback-log")
def log_playback(
    device_id: str,
    body: PlaybackBody,
    device: Device = Depends(get_device_by_token),
    db: Session = Depends(get_db),
):
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Token não corresponde ao dispositivo")
    if not body.campaign_id or not body.media_id:
        raise HTTPException(status_code=400, detail="campaign_id e media_id são obrigatórios")

    log = crud_playback_log.create_log(
        db,
        device_id=device_id,
        campaign_id=body.campaign_id,
        media_id=body.media_id,
        started_at=body.started_at,
        ended_at=body.ended_at,
        duration_ms=body.duration_ms,
        status=body.status,
    )
    return {"id": str(log.id), "status": log.status}


# ─── Admin: Pair confirm ──────────────────────────────────────────────────────

class PairConfirmBody(BaseModel):
    name: str
    device_type: Optional[str] = "tv"
    location: Optional[str] = None
    group: Optional[str] = None
    os: Optional[str] = None


@router.post("/{device_id}/pair-confirm", response_model=DeviceResponse)
def pair_confirm(
    device_id: str,
    body: PairConfirmBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")

    update_data = {"name": body.name, "device_type": body.device_type, "status": "online"}
    if body.location:
        update_data["location"] = body.location
    if body.os:
        update_data["os"] = body.os
    return crud_device.update(db, db_obj=device, obj_in=update_data)


# ─── Admin: Device metrics ────────────────────────────────────────────────────

@router.get("/{device_id}/metrics")
def get_device_metrics(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    views_today = (
        db.query(PlaybackLog)
        .filter(
            PlaybackLog.device_id == device_id,
            PlaybackLog.created_at >= today_start,
        )
        .count()
    )

    uptime_seconds = None
    if device.last_seen_at:
        delta = datetime.utcnow() - device.last_seen_at
        if delta.total_seconds() < 300:
            if device.last_connection:
                uptime_seconds = int((datetime.utcnow() - device.last_connection).total_seconds())

    return {
        "views_today": views_today,
        "uptime_seconds": uptime_seconds,
        "last_seen": device.last_seen_at,
        "current_media": device.current_campaign,
        "status": device.status.value if hasattr(device.status, "value") else device.status,
        "storage_used": device.storage_used,
        "player_version": device.player_version,
        "ip_address": device.ip_address,
    }


# ─── Admin: Send command ──────────────────────────────────────────────────────

VALID_COMMANDS = {
    "sync",
    "refresh_playlist",
    "clear_cache",
    "reload_player",
    "minimize_player",
    "restore_player",
    "show_desktop",
    "restart_app",
    "restart",
    "restart_device",
    "shutdown_device",
    "screenshot",
    "take_screenshot",
    "set_volume",
    "mute",
    "unmute",
}


def _validate_device_command_payload(command_type: str, payload: Optional[dict]) -> None:
    if command_type != "show_desktop":
        return

    duration = (payload or {}).get("duration_seconds", 10)
    if isinstance(duration, bool) or not isinstance(duration, (int, float)):
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="duration_seconds deve ser um numero entre 1 e 300.",
        )
    if duration < 1 or duration > 300:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="duration_seconds deve estar entre 1 e 300.",
        )


@router.get("/{device_id}/sessions", response_model=List[DeviceSessionResponse])
def list_device_sessions(
    device_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")

    sessions = (
        db.query(DeviceSession)
        .filter(DeviceSession.device_id == device_id)
        .order_by(DeviceSession.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return sessions


@router.post("/{device_id}/command", response_model=DeviceCommandResponse)
def send_device_command(
    device_id: str,
    body: DeviceCommandCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")

    if body.command_type not in VALID_COMMANDS:
        raise HTTPException(
            status_code=400,
            detail=f"Comando inválido. Válidos: {sorted(VALID_COMMANDS)}",
        )

    # SPEC 003 — comandos destrutivos exigem usuario identificado para auditoria.
    _validate_device_command_payload(body.command_type, body.payload)

    if body.command_type in DESTRUCTIVE_COMMAND_TYPES and not getattr(current_user, "email", None):
        raise HTTPException(
            status_code=403,
            detail="Comandos destrutivos exigem usuário autenticado com e-mail registrado.",
        )

    cmd = crud_device_command.create(
        db,
        device_id=device_id,
        tenant_id=str(device.tenant_id) if device.tenant_id else None,
        command_type=body.command_type,
        requested_by=current_user.email,
        payload=body.payload,
        expires_in_seconds=body.expires_in_seconds,
    )

    # SPEC 003 — notificar player em tempo real para nao esperar polling 10s.
    try:
        from services.event_bus import publish_device_event

        publish_device_event(
            str(device.id),
            event_type="command:new",
            data={
                "command_id": str(cmd.id),
                "command_type": cmd.command_type,
                "is_destructive": cmd.is_destructive,
            },
        )
    except Exception as exc:  # noqa: BLE001 — SSE eh best-effort
        print(f"[devices] command:new publish failed for {device.id}: {exc}")

    return cmd


@router.post("/{device_id}/commands/{command_id}/cancel", response_model=DeviceCommandResponse)
def cancel_device_command(
    device_id: str,
    command_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancela comando ainda nao executado.

    Permitido apenas para comandos em PENDING ou SENT. Comandos em
    RECEIVED/EXECUTING ja sao responsabilidade do player.
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")

    cmd = crud_device_command.get(db, command_id=command_id)
    if not cmd or str(cmd.device_id) != device_id:
        raise HTTPException(status_code=404, detail="Comando não encontrado")

    if cmd.status not in (DeviceCommandStatus.PENDING, DeviceCommandStatus.SENT):
        raise HTTPException(
            status_code=409,
            detail=f"Comando em estado {cmd.status} não pode ser cancelado.",
        )

    cmd = crud_device_command.cancel(db, obj=cmd)
    return cmd


@router.get("/{device_id}/commands", response_model=List[DeviceCommandResponse])
def list_device_commands(
    device_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")

    return crud_device_command.get_by_device(db, device_id=device_id, skip=skip, limit=limit)


@router.get("/{device_id}/commands/pending")
def get_pending_commands(
    device_id: str,
    device: Device = Depends(get_device_by_token),
    db: Session = Depends(get_db),
):
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Token não corresponde ao dispositivo")

    commands = crud_device_command.get_pending(db, device_id=device_id)
    response = [
        {
            "id": str(cmd.id),
            "command_type": cmd.command_type,
            "payload": cmd.payload,
            "requested_at": cmd.requested_at,
        }
        for cmd in commands
    ]
    crud_device_command.mark_many_sent(db, commands=commands)

    return response


@router.get("/{device_id}/playlist/updates")
async def playlist_updates_sse(
    device_id: str,
    db: Session = Depends(get_db),
    x_device_token: Optional[str] = Header(None, alias="X-Device-Token"),
    token: Optional[str] = Query(None),
):
    """SSE: real-time event stream for a device.

    Aceita o device token via header `X-Device-Token` ou query `?token=` —
    EventSource (browser) não permite headers customizados, então o player web
    autentica pela query string sobre HTTPS.

    Modelo: assina o canal Redis pub/sub `pw:device:{device_id}:events`.
    Eventos vêm do `services.event_bus` (publicados por endpoints HTTP e
    tasks Celery). Envia um snapshot inicial (estado atual da campanha) para
    o player reconciliar caso tenha perdido eventos durante a desconexão.

    Keep-alive (comentário SSE) a cada 25s para manter a conexão viva atrás
    de proxies (nginx default proxy_read_timeout=60s).
    """
    auth_token = x_device_token or token
    if not auth_token:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Device token ausente")
    device = crud_device.get_by_device_token(db, device_token=auth_token)
    if not device:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Device token inválido")
    if device.is_blocked:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Dispositivo bloqueado")
    if str(device.id) != device_id:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Token não corresponde ao dispositivo")

    from core.config import get_async_redis_client
    from services.event_bus import channel_for_device
    import asyncio

    channel = channel_for_device(str(device.id))

    snapshot_data = _build_snapshot(db, device)

    async def event_generator():
        redis_client = get_async_redis_client()
        if redis_client is None:
            yield {
                "event": "error",
                "data": json.dumps({"error": "redis_unavailable"}),
            }
            return

        # Snapshot inicial — estado atual de campanha + video_muted para
        # reconciliação no reconnect.
        yield {
            "event": "snapshot",
            "data": json.dumps(snapshot_data),
        }

        pubsub = redis_client.pubsub()
        try:
            await pubsub.subscribe(channel)
            keepalive_every = 25.0
            while True:
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True, timeout=keepalive_every),
                        timeout=keepalive_every + 1.0,
                    )
                except asyncio.TimeoutError:
                    message = None

                if message is None:
                    # Keep-alive: comentário SSE não dispara onmessage no client.
                    yield {"event": "ping", "data": "{}"}
                    continue

                payload = message.get("data")
                if not payload:
                    continue
                try:
                    envelope = json.loads(payload) if isinstance(payload, str) else payload
                except (TypeError, ValueError):
                    continue

                event_type = envelope.get("type", "message")
                yield {
                    "event": event_type,
                    "data": json.dumps(envelope),
                }
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            yield {
                "event": "error",
                "data": json.dumps({"error": str(exc)}),
            }
        finally:
            try:
                await pubsub.unsubscribe(channel)
            except Exception:  # noqa: BLE001
                pass
            for closer in ("aclose", "close"):
                fn = getattr(pubsub, closer, None)
                if fn is None:
                    continue
                try:
                    result = fn()
                    if hasattr(result, "__await__"):
                        await result
                    break
                except Exception:  # noqa: BLE001
                    pass
            for closer in ("aclose", "close"):
                fn = getattr(redis_client, closer, None)
                if fn is None:
                    continue
                try:
                    result = fn()
                    if hasattr(result, "__await__"):
                        await result
                    break
                except Exception:  # noqa: BLE001
                    pass

    return StreamingResponse(
        _sse_format(event_generator()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sync_device_config_version(db: Session, device: Device, response: dict) -> None:
    """Mantém device.config_version alinhado com o config_version da campanha servida.

    Sem isso, o heartbeat não consegue sinalizar `has_update` — ele compara a
    versão guardada no device com a versão atual da campanha.
    """
    campaign_payload = response.get("campaign") if isinstance(response, dict) else None
    target = campaign_payload.get("config_version") if isinstance(campaign_payload, dict) else None
    if device.config_version != target:
        device.config_version = target
        try:
            db.commit()
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            print(f"[playlist] config_version sync error: {exc}")


def _build_snapshot(db: Session, device: Device) -> dict:
    """Constrói o snapshot inicial enviado quando o SSE conecta."""
    campaign = _resolve_player_campaign(db, device=device)

    return {
        "campaign_id": str(campaign.id) if campaign else None,
        "config_version": campaign.config_version if campaign else None,
        "video_muted": (campaign.video_muted is not False) if campaign else True,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def _sse_format(generator):
    """Converte dicts {event, data} para o formato wire SSE (text/event-stream)."""
    async for chunk in generator:
        event = chunk.get("event", "message")
        data = chunk.get("data", "")
        yield f"event: {event}\ndata: {data}\n\n"


@router.post("/{device_id}/commands/{command_id}/ack")
def ack_device_command(
    device_id: str,
    command_id: str,
    body: DeviceCommandAck,
    device: Device = Depends(get_device_by_token),
    db: Session = Depends(get_db),
):
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Token não corresponde ao dispositivo")

    cmd = crud_device_command.get(db, command_id=command_id)
    if not cmd or str(cmd.device_id) != device_id:
        raise HTTPException(status_code=404, detail="Comando não encontrado")

    # `body.result` agora eh um CommandAckResult (Pydantic) ou None.
    # Serializa para dict antes de persistir no campo JSON.
    result_payload = None
    if body.result is not None:
        result_payload = body.result.model_dump(mode="json", exclude_none=True)

    cmd = crud_device_command.ack(
        db,
        obj=cmd,
        success=body.success,
        error_message=body.error_message,
        result=result_payload,
    )
    return {"ok": True, "status": cmd.status}


@router.post("/{device_id}/commands/{command_id}/received")
def mark_device_command_received(
    device_id: str,
    command_id: str,
    device: Device = Depends(get_device_by_token),
    db: Session = Depends(get_db),
):
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Token não corresponde ao dispositivo")
    cmd = crud_device_command.get(db, command_id=command_id)
    if not cmd or str(cmd.device_id) != device_id:
        raise HTTPException(status_code=404, detail="Comando não encontrado")
    cmd = crud_device_command.mark_received(db, obj=cmd)
    return {"ok": True, "status": cmd.status}


@router.post("/{device_id}/commands/{command_id}/started")
def mark_device_command_started(
    device_id: str,
    command_id: str,
    device: Device = Depends(get_device_by_token),
    db: Session = Depends(get_db),
):
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Token não corresponde ao dispositivo")
    cmd = crud_device_command.get(db, command_id=command_id)
    if not cmd or str(cmd.device_id) != device_id:
        raise HTTPException(status_code=404, detail="Comando não encontrado")
    cmd = crud_device_command.mark_executing(db, obj=cmd)
    return {"ok": True, "status": cmd.status}


# ─── Admin: Revoke device token ───────────────────────────────────────────────

@router.post("/{device_id}/revoke-token")
def revoke_device_token(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Legado — alias de POST /force-repair sem reason (SPEC 004).

    Comportamento atualizado: invalida o token atual (player antigo cai em
    401 e dispara forceRepair), incrementa token_version, marca
    requires_repairing, audita como `token_revoked` e publica SSE.

    Antes desta SPEC o endpoint gerava um novo token e devolvia para o admin —
    o que nao revogava o anterior nem invalidava o player. Por isso foi
    realinhado.
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")

    old_token_version = device.token_version or 1
    device.device_token = None
    device.token_version = old_token_version + 1
    device.requires_repairing = True

    revoked_count = _revoke_device_sessions(db, device.id)

    crud_device_pairing_event.log(
        db,
        device=device,
        event_type=DevicePairingEventType.TOKEN_REVOKED.value,
        requested_by_id=str(current_user.id),
        previous_token_version=old_token_version,
        new_token_version=device.token_version,
        metadata={"revoked_sessions_count": revoked_count},
        commit=False,
    )

    db.add(device)
    db.commit()
    db.refresh(device)
    _invalidate_device_playlist_cache(device_id=str(device.id))
    _publish_pairing_revoked(device.id, "token_revoked")

    return {
        "ok": True,
        "token_version": device.token_version,
        "revoked_sessions_count": revoked_count,
    }


# ─── TASK 08: Debug de Spots ──────────────────────────────────────────────────

@router.get("/{device_id}/debug-spots")
def debug_device_spots(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Diagnostica problemas com spots não tocando.

    Retorna:
    - Todos os spots agendados na playlist do dispositivo
    - Quais estão elegíveis agora
    - Por que outros foram rejeitados
    - Próximo spot que deve tocar

    TASK 08: Logs estruturados para diagnosticar spots.
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")

    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")

    now = schedule_now()

    # Obter playlist ativa do dispositivo
    playlist = device.audio_playlist if device.audio_playlist_id else None

    if not playlist:
        return {
            "timestamp": now.isoformat(),
            "device_id": str(device.id),
            "device_name": device.name,
            "error": "Dispositivo não tem playlist sonora configurada",
        }

    # Obter TODOS os agendamentos de spot (mesmo inativos)
    all_schedules = (
        db.query(AudioSpotSchedule)
        .filter(AudioSpotSchedule.playlist_id == str(playlist.id))
        .all()
    )

    spot_diagnostics = []

    for schedule in all_schedules:
        spot = db.query(AudioSpot).filter(AudioSpot.id == schedule.spot_id).first()
        if not spot:
            spot_diagnostics.append({
                "schedule_id": str(schedule.id),
                "status": "ERROR",
                "reason": "Spot não encontrado",
                "spot_id": str(schedule.spot_id),
            })
            continue

        # Verificar por que está ou não elegível
        from services.audio_spot_scheduler import get_eligible_spots

        eligible_spots = get_eligible_spots(db, playlist_id=str(playlist.id), now=now)
        is_eligible = any(s[0].id == spot.id for s in eligible_spots)

        diagnosis = {
            "spot_id": str(spot.id),
            "spot_name": spot.name,
            "schedule_id": str(schedule.id),
            "is_schedule_active": schedule.is_active,
            "is_spot_active": spot.status.value if hasattr(spot.status, "value") else spot.status,
            "interval_seconds": schedule.interval_seconds,
            "priority": schedule.priority,
            "insertion_policy": spot.insertion_policy.value if hasattr(spot.insertion_policy, "value") else spot.insertion_policy,
            "eligible_now": is_eligible,
            "start_time": schedule.start_time,
            "end_time": schedule.end_time,
            "starts_at": schedule.starts_at.isoformat() if schedule.starts_at else None,
            "ends_at": schedule.ends_at.isoformat() if schedule.ends_at else None,
        }

        # Diagnosticar por que não é elegível
        if not is_eligible:
            reasons = []

            if not schedule.is_active:
                reasons.append("Agendamento inativo")

            if spot.status.value != "active" if hasattr(spot.status, "value") else spot.status != "active":
                reasons.append(f"Spot inativo ({spot.status})")

            # Verificar tempo
            current_time = now.time()

            if schedule.start_time or schedule.end_time:
                from services.audio_spot_scheduler import parse_time_str
                start_t = parse_time_str(schedule.start_time) if schedule.start_time else None
                end_t = parse_time_str(schedule.end_time) if schedule.end_time else None

                if start_t and current_time < start_t:
                    reasons.append(f"Antes do horário ({schedule.start_time})")
                elif end_t and current_time >= end_t:
                    reasons.append(f"Depois do horário ({schedule.end_time})")

            # Verificar período (datetime-preciso, igual ao spot_resolver real)
            if schedule.starts_at and now < schedule.starts_at:
                reasons.append(f"Ainda não começou (inicia em {schedule.starts_at.isoformat()})")
            elif schedule.ends_at and now > schedule.ends_at:
                reasons.append(f"Já terminou (terminou em {schedule.ends_at.isoformat()})")

            diagnosis["why_not_eligible"] = reasons if reasons else ["Razão desconhecida"]

        spot_diagnostics.append(diagnosis)

    # Próximo spot que deve tocar
    from services.audio_spot_scheduler import get_next_spot_time
    next_spot_result = get_next_spot_time(db, playlist_id=str(playlist.id), now=now)

    next_spot_info = None
    if next_spot_result:
        spot_time, spot, schedule = next_spot_result
        time_until = (spot_time - now).total_seconds()
        next_spot_info = {
            "spot_id": str(spot.id),
            "spot_name": spot.name,
            "will_play_at": spot_time.isoformat(),
            "seconds_until_play": time_until,
            "interval_seconds": schedule.interval_seconds,
            "priority": schedule.priority,
        }

    return {
        "timestamp": now.isoformat(),
        "device": {
            "device_id": str(device.id),
            "device_name": device.name,
        },
        "playlist": {
            "playlist_id": str(playlist.id),
            "playlist_name": playlist.name,
        },
        "total_spot_schedules": len(all_schedules),
        "eligible_now_count": sum(1 for d in spot_diagnostics if d.get("eligible_now")),
        "spot_diagnostics": spot_diagnostics,
        "next_spot_due": next_spot_info,
        "info": "Use para diagnosticar por que spots não tocam. Procure 'eligible_now': false com 'why_not_eligible'",
    }
