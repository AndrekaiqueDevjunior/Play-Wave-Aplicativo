import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.dependencies import get_current_user
from core.models import User, Device
from core.schemas_completos import (
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceStatusEnum,
    DevicePairingCodeCreate, PlaybackLogCreate,
)
from crud.entidades import crud_device, crud_device_pairing_code, crud_playback_log, crud_campaign


# ─── Device-token dependency ─────────────────────────────────────────────────

def get_device_by_token(
    x_device_token: str = Header(..., alias="X-Device-Token"),
    db: Session = Depends(get_db),
) -> Device:
    device = crud_device.get_by_device_token(db, device_token=x_device_token)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device token inválido",
        )
    if device.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dispositivo bloqueado",
        )
    return device

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/", response_model=List[DeviceResponse])
def get_devices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    status: Optional[DeviceStatusEnum] = Query(None),
    device_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None)
):
    """
    Lista dispositivos com filtros opcionais
    """
    # Se não for admin, filtra apenas do tenant do usuário
    if current_user.role != "admin" and not tenant_id:
        tenant_id = str(current_user.tenant_id)
    
    # Aplicar filtros específicos
    if status:
        devices = crud_device.get_by_status(db, status=status)
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
    
    return devices


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str
):
    """
    Obtém dispositivo por ID
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar este dispositivo"
        )
    
    return device


@router.post("/", response_model=DeviceResponse)
def create_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_in: DeviceCreate
):
    """
    Cria novo dispositivo
    """
    # Verificar se código de pareamento já existe
    existing_device = crud_device.get_by_pairing_code(db, pairing_code=device_in.pairing_code)
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de pareamento já existe"
        )
    
    # Atribuir tenant se não for admin
    if current_user.role != "admin":
        device_in.tenant_id = current_user.tenant_id
    
    device = crud_device.create(db, obj_in=device_in)
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
    device_in: DeviceUpdate
):
    """
    Atualiza dispositivo
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar este dispositivo"
        )
    
    # Verificar se novo código de pareamento já existe
    if device_in.pairing_code and device_in.pairing_code != device.pairing_code:
        existing_device = crud_device.get_by_pairing_code(db, pairing_code=device_in.pairing_code)
        if existing_device:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de pareamento já existe"
            )
    
    device = crud_device.update(db, db_obj=device, obj_in=device_in)
    return device


@router.delete("/{device_id}")
def delete_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str
):
    """
    Remove dispositivo
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para remover este dispositivo"
        )
    
    crud_device.remove(db, id=device_id)
    return {"message": "Dispositivo removido com sucesso"}


@router.patch("/{device_id}/status")
def update_device_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
    status: DeviceStatusEnum
):
    """
    Atualiza status do dispositivo
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar este dispositivo"
        )
    
    device = crud_device.update_status(db, db_obj=device, status=status)
    return {"message": f"Status atualizado para {status}"}


@router.post("/{device_id}/block")
def block_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str
):
    """
    Bloqueia dispositivo
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para bloquear este dispositivo"
        )
    
    device = crud_device.block_device(db, db_obj=device)
    return {"message": "Dispositivo bloqueado com sucesso"}


@router.post("/{device_id}/unblock")
def unblock_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str
):
    """
    Desbloqueia dispositivo
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para desbloquear este dispositivo"
        )
    
    device = crud_device.unblock_device(db, db_obj=device)
    return {"message": "Dispositivo desbloqueado com sucesso"}


@router.get("/statistics/overview")
def get_device_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém estatísticas dos dispositivos
    """
    # Se não for admin, filtra apenas do tenant do usuário
    tenant_id = None if current_user.role == "admin" else str(current_user.tenant_id)
    
    statistics = crud_device.get_statistics(db, tenant_id=tenant_id)
    return statistics


@router.get("/online/list", response_model=List[DeviceResponse])
def get_online_devices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista dispositivos online
    """
    devices = crud_device.get_online(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        devices = [d for d in devices if str(d.tenant_id) == str(current_user.tenant_id)]
    
    return devices[skip:skip+limit]


@router.get("/offline/list", response_model=List[DeviceResponse])
def get_offline_devices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista dispositivos offline
    """
    devices = crud_device.get_offline(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        devices = [d for d in devices if str(d.tenant_id) == str(current_user.tenant_id)]
    
    return devices[skip:skip+limit]


@router.get("/pairing/waiting", response_model=List[DeviceResponse])
def get_waiting_pairing_devices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    devices = crud_device.get_waiting_pairing(db)
    if current_user.role != "admin":
        devices = [d for d in devices if str(d.tenant_id) == str(current_user.tenant_id)]
    return devices[skip:skip+limit]


# ─── Player TV endpoints (unauthenticated / device-token) ────────────────────

class PairRequestBody(BaseModel):
    player_version: Optional[str] = None
    os: Optional[str] = None


@router.post("/pair-request")
def pair_request(body: PairRequestBody, db: Session = Depends(get_db)):
    from datetime import timedelta
    code = secrets.token_hex(3).upper()  # e.g. "A1B2C3"
    # expires_at will be overridden inside create_code (10 min); pass placeholder
    placeholder_expiry = datetime.utcnow() + timedelta(minutes=10)
    obj_in = DevicePairingCodeCreate(
        code=code,
        expires_at=placeholder_expiry,
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
    if not pairing:
        raise HTTPException(status_code=404, detail="Código não encontrado")
    if pairing.expires_at and pairing.expires_at < datetime.utcnow():
        return {"status": "expired", "device_id": None, "device_token": None}

    result: dict = {"status": pairing.status, "device_id": None, "device_token": None}
    if pairing.status == "paired" and pairing.device_id:
        device = crud_device.get(db, id=str(pairing.device_id))
        if device:
            result["device_id"] = str(device.id)
            result["device_token"] = device.device_token
    return result


@router.get("/{device_id}/playlist")
def get_device_playlist(
    device_id: str,
    device: Device = Depends(get_device_by_token),
    db: Session = Depends(get_db),
):
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Token não corresponde ao dispositivo")

    # Update last seen
    crud_device.update_last_seen(db, db_obj=device)

    if not device.current_campaign_id:
        return {"campaign": None, "media": [], "audio_playlist": None}

    campaign = crud_campaign.get(db, id=str(device.current_campaign_id))
    if not campaign:
        return {"campaign": None, "media": [], "audio_playlist": None}

    return {
        "campaign": {
            "id": str(campaign.id),
            "name": campaign.name,
            "media_ids": campaign.media_ids or [],
            "media_order": campaign.media_order or [],
            "schedule_all_day": campaign.schedule_all_day,
            "schedule_days": campaign.schedule_days,
            "schedule_start_time": campaign.schedule_start_time,
            "schedule_end_time": campaign.schedule_end_time,
            "config_version": campaign.config_version,
        },
        "audio_playlist": {
            "id": str(device.audio_playlist_id),
            "name": device.audio_playlist_name,
            "volume": device.audio_volume,
        } if device.audio_playlist_id else None,
    }


class HeartbeatBody(BaseModel):
    ip_address: Optional[str] = None
    player_version: Optional[str] = None
    storage_used: Optional[int] = None


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


class PlaybackBody(BaseModel):
    campaign_id: Optional[str] = None
    media_id: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str = "completed"


@router.post("/{device_id}/playback-log")
def log_playback(
    device_id: str,
    body: PlaybackBody,
    device: Device = Depends(get_device_by_token),
    db: Session = Depends(get_db),
):
    if str(device.id) != device_id:
        raise HTTPException(status_code=403, detail="Token não corresponde ao dispositivo")

    log = crud_playback_log.create_log(
        db,
        device_id=device_id,
        campaign_id=body.campaign_id or "",
        media_id=body.media_id or "",
        started_at=body.started_at,
        ended_at=body.ended_at,
        duration_ms=body.duration_ms,
        status=body.status,
    )
    return {"id": str(log.id), "status": log.status}
