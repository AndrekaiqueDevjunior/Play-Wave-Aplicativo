import json
import secrets
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi.responses import StreamingResponse

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi import status as http_status
from pydantic import BaseModel
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from core.models import (
    AudioPlaylist,
    AudioPlaylistStatus,
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
    DeviceSession,
    Media,
    PlaybackLog,
    User,
    ViewReport,
)
from core.schemas_completos import (
    DeviceCommandAck,
    DeviceCommandCreate,
    DeviceCommandResponse,
    DeviceCreate,
    DevicePairingCodeCreate,
    DeviceResponse,
    DeviceSessionResponse,
    DeviceStatusEnum,
    DeviceUpdate,
)
from crud.entidades.crud_device_command import crud_device_command
from crud.entidades.crud_campaign import crud_campaign
from crud.entidades.crud_device import crud_device
from crud.entidades.crud_device_pairing_code import crud_device_pairing_code
from crud.entidades.crud_playback_log import crud_playback_log


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

def get_device_by_token(
    x_device_token: str = Header(..., alias="X-Device-Token"),
    db: Session = Depends(get_db),
) -> Device:
    device = crud_device.get_by_device_token(db, device_token=x_device_token)
    if not device:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Device token inválido",
        )
    if device.is_blocked:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Dispositivo bloqueado",
        )
    if getattr(device, "requires_repairing", False):
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Dispositivo requer novo pareamento",
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


def _campaign_payload(campaign: Campaign) -> dict:
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
) -> List[dict]:
    entries = _resolve_playlist_entries(db, campaign=campaign)
    if not entries:
        return []

    media_ids = {media_id for _, media_id in entries}
    media_items = db.query(Media).filter(Media.id.in_(media_ids)).all()
    media_by_id = {str(media.id): media for media in media_items}

    payload: List[dict] = []
    now = datetime.utcnow()
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


def _build_audio_playlist_from_model(playlist: AudioPlaylist, db: Session) -> Optional[dict]:
    if not playlist.track_ids:
        return {
            "id": str(playlist.id),
            "name": playlist.name,
            "volume": playlist.volume_default,
            "loop": playlist.loop_enabled,
            "shuffle": playlist.shuffle_enabled,
            "tracks": [],
        }
    tracks = db.query(AudioTrack).filter(
        AudioTrack.id.in_([str(tid) for tid in playlist.track_ids]),
        AudioTrack.status == AudioTrackStatus.ACTIVE,
    ).all()
    track_map = {str(t.id): t for t in tracks}
    ordered = []
    for tid in playlist.track_ids:
        t = track_map.get(str(tid))
        if t:
            ordered.append({
                "id": str(t.id),
                "name": t.name,
                "file_url": t.file_url,
                "duration_seconds": t.duration_seconds or 0,
                "volume": (playlist.track_volumes or {}).get(str(t.id), playlist.volume_default),
            })
    return {
        "id": str(playlist.id),
        "name": playlist.name,
        "volume": playlist.volume_default,
        "loop": playlist.loop_enabled,
        "shuffle": playlist.shuffle_enabled,
        "tracks": ordered,
    }


def _build_audio_playlist(device: Device, db: Session) -> Optional[dict]:
    if not device.audio_playlist_id:
        return None
    playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == device.audio_playlist_id).first()
    if not playlist or playlist.status != AudioPlaylistStatus.ACTIVE:
        return None
    if not playlist.track_ids:
        return {
            "id": str(playlist.id),
            "name": playlist.name,
            "volume": playlist.volume_default,
            "loop": playlist.loop_enabled,
            "shuffle": playlist.shuffle_enabled,
            "tracks": [],
        }
    tracks = db.query(AudioTrack).filter(
        AudioTrack.id.in_([str(tid) for tid in playlist.track_ids]),
        AudioTrack.status == AudioTrackStatus.ACTIVE,
    ).all()
    track_map = {str(t.id): t for t in tracks}
    ordered = []
    for tid in playlist.track_ids:
        t = track_map.get(str(tid))
        if t:
            ordered.append({
                "id": str(t.id),
                "name": t.name,
                "file_url": t.file_url,
                "duration_seconds": t.duration_seconds or 0,
                "volume": (playlist.track_volumes or {}).get(str(t.id), playlist.volume_default),
            })
    return {
        "id": str(playlist.id),
        "name": playlist.name,
        "volume": playlist.volume_default,
        "loop": playlist.loop_enabled,
        "shuffle": playlist.shuffle_enabled,
        "tracks": ordered,
    }


def _resolve_player_campaign(db: Session, *, device: Device) -> Optional[Campaign]:
    if device.current_campaign_id:
        campaign = crud_campaign.get(db, id=str(device.current_campaign_id))
        if campaign:
            return campaign
    return crud_campaign.get_active_for_device(db, device_id=str(device.id))


def _build_player_playlist_response(db: Session, *, device: Device) -> dict:
    campaign = _resolve_player_campaign(db, device=device)
    if not campaign:
        return {
            "device_name": device.name,
            "campaign": None,
            "media": [],
            "audio_playlist": _build_audio_playlist(device, db),
        }

    audio_playlist = None
    if campaign.audio_playlist_id:
        playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == campaign.audio_playlist_id).first()
        if playlist and playlist.status == AudioPlaylistStatus.ACTIVE:
            audio_playlist = _build_audio_playlist_from_model(playlist, db)
    elif device.audio_playlist_id:
        audio_playlist = _build_audio_playlist(device, db)

    return {
        "device_name": device.name,
        "campaign": _campaign_payload(campaign),
        "media": _build_media_payload(db, campaign=campaign),
        "audio_playlist": audio_playlist,
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


@router.get("/by-code/{code}/status")
def check_pairing_status(code: str, db: Session = Depends(get_db)):
    pairing = crud_device_pairing_code.get_by_code(db, code=code)
    if pairing:
        # Always check if admin already created a matching device regardless of pairing status.
        # This handles the "admin-first" flow where create_device ran before pair_request.
        device_for_code = crud_device.get_by_pairing_code(db, pairing_code=code)

        if pairing.expires_at and pairing.expires_at < datetime.utcnow():
            # Expired but device may already exist
            if device_for_code and device_for_code.device_token:
                return {"status": "paired", "device_id": str(device_for_code.id), "device_token": device_for_code.device_token}
            return {"status": "expired", "device_id": None, "device_token": None}

        # If DevicePairingCode is still "waiting" but admin already created the device
        if pairing.status == "waiting" and device_for_code and device_for_code.device_token:
            print(f"[pairing] auto-linking code={code} to device={device_for_code.id}")
            pairing.status = "paired"
            pairing.device_id = device_for_code.id
            pairing.used_at = datetime.utcnow()
            db.commit()
            return {"status": "paired", "device_id": str(device_for_code.id), "device_token": device_for_code.device_token}
        if pairing.status == "waiting" and device_for_code and not device_for_code.device_token:
            device_for_code.device_token = secrets.token_urlsafe(32)
            device_for_code.requires_repairing = False
            device_for_code.status = "online"
            device_for_code.paired_at = datetime.utcnow()
            pairing.status = "paired"
            pairing.device_id = device_for_code.id
            pairing.used_at = datetime.utcnow()
            db.commit()
            db.refresh(device_for_code)
            return {"status": "paired", "device_id": str(device_for_code.id), "device_token": device_for_code.device_token}

        result: dict = {"status": pairing.status, "device_id": None, "device_token": None}
        if pairing.status == "paired" and pairing.device_id:
            device = crud_device.get(db, id=str(pairing.device_id))
            if device:
                result["device_id"] = str(device.id)
                result["device_token"] = device.device_token
        print(f"[pairing] code={code} status={result['status']}")
        return result

    # Fallback: player polling a code that was never registered (admin-first, no pair_request yet)
    device = crud_device.get_by_pairing_code(db, pairing_code=code)
    if not device:
        raise HTTPException(status_code=404, detail="Código não encontrado")

    if device.is_blocked:
        return {"status": "expired", "device_id": None, "device_token": None}

    if device.device_token:
        print(f"[pairing] code={code} fallback direct device match id={device.id}")
        return {"status": "paired", "device_id": str(device.id), "device_token": device.device_token}

    if device.status == "waiting_pairing":
        device.device_token = secrets.token_urlsafe(32)
        device.requires_repairing = False
        device.paired_at = datetime.utcnow()
        db.commit()
        db.refresh(device)
        return {"status": "paired", "device_id": str(device.id), "device_token": device.device_token}

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

    response = _build_player_playlist_response(db, device=device)

    _sync_device_config_version(db, device, response)

    if redis_client:
        try:
            redis_client.setex(cache_key, 30, json.dumps(response))
        except Exception as e:
            print(f"[playlist] Redis set error: {e}")

    return response


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
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
            detail="Sem permissão para acessar este dispositivo",
        )
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
        if any(field in device_in.model_fields_set for field in ("current_campaign_id", "audio_playlist_id", "pairing_code")):
            _invalidate_device_playlist_cache(device_id=str(device.id))
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
    return {"message": "Dispositivo desbloqueado com sucesso"}


@router.post("/{device_id}/pairing-code/regenerate", response_model=DeviceResponse)
def regenerate_pairing_code(
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

    device.pairing_code = next_code
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
    db.add(device)
    db.commit()
    db.refresh(device)
    _invalidate_device_playlist_cache(device_id=str(device.id))
    return device


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
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Dispositivo não encontrado")
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")

    new_token = secrets.token_urlsafe(32)
    crud_device.update(db, db_obj=device, obj_in={"device_token": new_token})
    return {"new_token": new_token}
