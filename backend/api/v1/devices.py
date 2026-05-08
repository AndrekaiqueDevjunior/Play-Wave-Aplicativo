import secrets
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi import status as http_status
from pydantic import BaseModel
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from core.models import Device, Media, User
from core.schemas_completos import (
    DeviceCreate,
    DevicePairingCodeCreate,
    DeviceResponse,
    DeviceStatusEnum,
    DeviceUpdate,
)
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


def _build_audio_playlist(device: Device) -> Optional[dict]:
    if not device.audio_playlist_id:
        return None
    return {
        "id": str(device.audio_playlist_id),
        "name": device.audio_playlist_name,
        "volume": device.audio_volume,
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
        if pairing.expires_at and pairing.expires_at < datetime.utcnow():
            return {"status": "expired", "device_id": None, "device_token": None}
        result: dict = {"status": pairing.status, "device_id": None, "device_token": None}
        if pairing.status == "paired" and pairing.device_id:
            device = crud_device.get(db, id=str(pairing.device_id))
            if device:
                result["device_id"] = str(device.id)
                result["device_token"] = device.device_token
        return result

    # Fallback: admin may have created the device directly via the panel
    device = crud_device.get_by_pairing_code(db, pairing_code=code)
    if not device:
        raise HTTPException(status_code=404, detail="Código não encontrado")

    if device.is_blocked:
        return {"status": "expired", "device_id": None, "device_token": None}

    # Already has a token — pairing is complete
    if device.device_token:
        return {"status": "paired", "device_id": str(device.id), "device_token": device.device_token}

    # Admin created the device and is waiting for the player — generate token on first poll
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

    if not device.current_campaign_id:
        return {
            "device_name": device.name,
            "campaign": None,
            "media": [],
            "audio_playlist": _build_audio_playlist(device),
        }

    campaign = crud_campaign.get(db, id=str(device.current_campaign_id))
    if not campaign:
        return {
            "device_name": device.name,
            "campaign": None,
            "media": [],
            "audio_playlist": _build_audio_playlist(device),
        }

    media_order = campaign.media_order or []
    ordered_ids = [
        item.get("media_id") if isinstance(item, dict) else item
        for item in media_order
    ] or campaign.media_ids or []

    media_by_id: dict = {}
    if ordered_ids:
        media_items = db.query(Media).filter(Media.id.in_(ordered_ids)).all()
        media_by_id = {str(m.id): m for m in media_items}

    return {
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
        "audio_playlist": _build_audio_playlist(device),
    }


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
    return device


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
    if device.status != "online":
        crud_device.update_status(db, db_obj=device, status="online")

    return {"status": "ok", "server_time": datetime.utcnow().isoformat()}


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


