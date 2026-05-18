import secrets
import json
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
    Device,
    DeviceCommand,
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
    current_media_name: Optional[str] = None


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
    return device


router = APIRouter(prefix="/devices", tags=["devices"])


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _clean_uuid_fields(data: dict) -> dict:
    """Convert empty strings to None for UUID-typed fields."""
    for field in ("audio_playlist_id", "current_campaign_id"):
        if data.get(field) == "":
            data[field] = None
    return data


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

    crud_device.update_last_seen(db, db_obj=device)

    # Check Redis cache first
    from core.config import get_redis_client
    import json
    redis_client = get_redis_client()
    cache_key = f"device_playlist:{device_id}"
    
    if redis_client:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                print(f"[playlist] device={device.id} cache hit")
                return json.loads(cached)
        except Exception as e:
            print(f"[playlist] Redis error: {e}")

    # 1. Try explicit current_campaign_id on device
    campaign = None
    if device.current_campaign_id:
        campaign = crud_campaign.get(db, id=str(device.current_campaign_id))
        print(f"[playlist] device={device.id} current_campaign_id={device.current_campaign_id} found={campaign is not None}")

    # 2. Fallback: find active campaign that targets this device via device_ids
    if not campaign:
        campaign = crud_campaign.get_active_for_device(db, device_id=str(device.id))
        print(f"[playlist] device={device.id} fallback campaign={campaign.id if campaign else None}")

    if not campaign:
        print(f"[playlist] device={device.id} no active campaign found")
        response = {
            "device_name": device.name,
            "campaign": None,
            "media": [],
            "audio_playlist": _build_audio_playlist(device, db),
        }
        # Cache empty response for 30 seconds
        if redis_client:
            try:
                redis_client.setex(cache_key, 30, json.dumps(response))
            except Exception as e:
                print(f"[playlist] Redis set error: {e}")
        return response

    media_order = campaign.media_order or []
    ordered_ids = [
        item.get("media_id") if isinstance(item, dict) else item
        for item in media_order
    ] or campaign.media_ids or []

    media_by_id: dict = {}
    if ordered_ids:
        media_items = db.query(Media).filter(Media.id.in_(ordered_ids)).all()
        media_by_id = {str(m.id): m for m in media_items}

    # Use campaign's audio playlist if set, otherwise fall back to device's
    audio_playlist_source = campaign.audio_playlist_id or device.audio_playlist_id
    audio_playlist = None
    if audio_playlist_source:
        # If campaign has its own playlist, build from campaign
        if campaign.audio_playlist_id:
            playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == campaign.audio_playlist_id).first()
            if playlist and playlist.status == AudioPlaylistStatus.ACTIVE:
                audio_playlist = _build_audio_playlist_from_model(playlist, db)
        else:
            # Otherwise use device's playlist
            audio_playlist = _build_audio_playlist(device, db)

    response = {
        "device_name": device.name,
        "campaign": {
            "id": str(campaign.id),
            "name": campaign.name,
            "media_ids": campaign.media_ids or [],
            "media_order": campaign.media_order or [],
            "schedule_all_day": campaign.schedule_all_day,
            "schedule_days": campaign.schedule_days,
            "schedule_start_time": str(campaign.schedule_start_time) if campaign.schedule_start_time else None,
            "schedule_end_time": str(campaign.schedule_end_time) if campaign.schedule_end_time else None,
            "config_version": campaign.config_version,
        },
        "media": [
            {
                "id": str(m.id),
                "name": m.name,
                "type": m.type.value if hasattr(m.type, "value") else m.type,
                "file_url": m.file_url,
                "duration": m.duration or 10,
                "mime_type": m.mime_type,
                "status": m.status.value if hasattr(m.status, "value") else m.status,
            }
            for media_id in ordered_ids
            if (m := media_by_id.get(str(media_id)))
        ],
        "audio_playlist": audio_playlist,
    }

    # Cache response for 30 seconds (short TTL to allow quick updates)
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
    if device_in.pairing_code and device_in.pairing_code != device.pairing_code:
        if crud_device.get_by_pairing_code(db, pairing_code=device_in.pairing_code):
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail="Código de pareamento já existe",
            )

    update_data = _clean_uuid_fields(device_in.model_dump(exclude_unset=True))
    try:
        for field, value in update_data.items():
            setattr(device, field, value)
        db.commit()
        db.refresh(device)
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


@router.post("/{device_id}/heartbeat")
def device_heartbeat(
    device_id: str,
    body: HeartbeatBody,
    device: Device = Depends(get_device_by_token),
    db: Session = Depends(get_db),
):
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Token não corresponde ao dispositivo")

    crud_device.update_last_seen(db, db_obj=device, ip_address=body.ip_address)

    if body.player_version:
        device.player_version = body.player_version
    if body.storage_used is not None:
        device.storage_used = body.storage_used
    if body.current_campaign_id is not None:
        device.current_campaign_id = body.current_campaign_id or None
    if body.current_media_name is not None:
        device.current_campaign = body.current_media_name
    if device.status != "online":
        device.status = "online"
    db.commit()
    db.refresh(device)

    pending_count = db.query(DeviceCommand).filter(
        DeviceCommand.device_id == device_id,
        DeviceCommand.status == "pending",
    ).count()

    return {
        "ok": True,
        "is_blocked": device.is_blocked,
        "config_version": device.config_version,
        "has_update": False,
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

VALID_COMMANDS = {"restart", "sync", "clear_cache", "screenshot", "refresh_playlist"}


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

    cmd = crud_device_command.create(
        db,
        device_id=device_id,
        tenant_id=str(device.tenant_id) if device.tenant_id else None,
        command_type=body.command_type,
        requested_by=current_user.email,
        payload=body.payload,
    )
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
    for cmd in commands:
        crud_device_command.mark_sent(db, obj=cmd)

    return [
        {
            "id": str(cmd.id),
            "command_type": cmd.command_type,
            "payload": cmd.payload,
            "requested_at": cmd.requested_at,
        }
        for cmd in commands
    ]


@router.get("/{device_id}/playlist/updates")
async def playlist_updates_sse(
    device_id: str,
    device: Device = Depends(get_device_by_token),
    db: Session = Depends(get_db),
):
    """SSE endpoint for real-time playlist updates based on config_version changes."""
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Token não corresponde ao dispositivo")

    from core.config import get_redis_client
    import asyncio

    redis_client = get_redis_client()
    
    async def event_generator():
        last_config_version = None
        
        while True:
            try:
                # Get current campaign and its config_version
                campaign = None
                if device.current_campaign_id:
                    from core.models import Campaign
                    campaign = db.query(Campaign).filter(Campaign.id == device.current_campaign_id).first()
                
                if not campaign:
                    from crud.entidades.crud_campaign import crud_campaign
                    campaign = crud_campaign.get_active_for_device(db, device_id=str(device.id))
                
                current_config_version = campaign.config_version if campaign else None
                
                # If config_version changed, send update
                if last_config_version != current_config_version:
                    last_config_version = current_config_version
                    yield {
                        "event": "playlist_update",
                        "data": json.dumps({
                            "config_version": current_config_version,
                            "timestamp": datetime.utcnow().isoformat(),
                            "campaign_id": str(campaign.id) if campaign else None,
                        })
                    }
                
                # Wait 5 seconds before checking again
                await asyncio.sleep(5)
            except Exception as e:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)})
                }
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


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

    cmd = crud_device_command.ack(db, obj=cmd, success=body.success, error_message=body.error_message)
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

