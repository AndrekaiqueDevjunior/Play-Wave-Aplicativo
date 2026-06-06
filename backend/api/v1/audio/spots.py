import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.dependencies import get_current_user
from core.models import AudioSpot, AudioTrack, AudioPlaylist, Campaign, Device, User
from core.schemas_completos import (
    AudioSpotCreate,
    AudioSpotResponse,
    AudioSpotStatusEnum,
    AudioSpotUpdate,
    AudioSpotScheduleCreate,
    AudioSpotScheduleResponse,
    AudioSpotScheduleUpdate,
)
from crud.entidades import crud_audio_spot, crud_audio_spot_schedule, crud_audio_playlist

router = APIRouter(prefix="/audio/spots", tags=["audio-spots"])
log = logging.getLogger("playwave.spots")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _invalidate_device_playlist_cache(device_ids: Optional[set] = None) -> None:
    from core.config import get_redis_client
    redis_client = get_redis_client()
    if not redis_client:
        return
    try:
        if device_ids is not None:
            if not device_ids:
                return
            pipe = redis_client.pipeline(transaction=False)
            for device_id in device_ids:
                pipe.delete(f"device_playlist:{device_id}")
            pipe.execute()
            return
        for key in redis_client.scan_iter("device_playlist:*"):
            redis_client.delete(key)
    except Exception as exc:
        log.warning("Redis cache invalidation error: %s", exc)


def _device_ids_for_playlist(db: Session, *, playlist_id: str) -> set:
    device_ids = {
        str(row.id)
        for row in db.query(Device.id).filter(Device.audio_playlist_id == playlist_id).all()
    }
    campaigns = db.query(Campaign).filter(Campaign.audio_playlist_id == playlist_id).all()
    for campaign in campaigns:
        device_ids.update(str(d) for d in (campaign.device_ids or []) if d)
        rows = db.query(Device.id).filter(Device.current_campaign_id == campaign.id).all()
        device_ids.update(str(row.id) for row in rows)
    return device_ids


def _authorize_spot_access(db: Session, *, spot_id: str, current_user: User) -> AudioSpot:
    spot = crud_audio_spot.get(db, id=spot_id)
    if not spot:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Spot de áudio não encontrado")
    if current_user.role != "admin" and str(spot.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, detail="Sem permissão para acessar este spot")
    return spot


def _ensure_track_in_spot_scope(db: Session, *, track_id: str, current_user: User) -> AudioTrack:
    track = db.query(AudioTrack).filter(AudioTrack.id == track_id).first()
    if not track:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Faixa de áudio não encontrada")
    if current_user.role != "admin" and str(track.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, detail="Sem permissão para usar esta faixa")
    return track


def _effective_tenant_id(current_user: User, explicit: Optional[str] = None) -> Optional[str]:
    """Resolve tenant_id efetivo: admin pode passar explícito, outros usam o próprio."""
    if current_user.role == "admin":
        return explicit or str(current_user.tenant_id)
    return str(current_user.tenant_id)


def _validate_cross_tenant(
    db: Session,
    *,
    tenant_id: str,
    playlist_id: Optional[str],
    campaign_id: Optional[str],
    device_id: Optional[str],
    spot_id: Optional[str],
) -> None:
    """Garante que todos os escopos pertencem ao mesmo tenant."""

    def _err(entity: str) -> HTTPException:
        return HTTPException(
            http_status.HTTP_403_FORBIDDEN,
            detail=f"{entity} pertence a outro tenant. Vínculos cross-tenant não são permitidos.",
        )

    if spot_id:
        spot = db.query(AudioSpot).filter(AudioSpot.id == spot_id).first()
        if spot and spot.tenant_id and str(spot.tenant_id) != tenant_id:
            raise _err("Spot")

    if playlist_id:
        playlist = db.query(AudioPlaylist).filter(AudioPlaylist.id == playlist_id).first()
        if playlist and playlist.tenant_id and str(playlist.tenant_id) != tenant_id:
            raise _err("Playlist")

    if campaign_id:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Campanha não encontrada")
        if campaign.tenant_id and str(campaign.tenant_id) != tenant_id:
            raise _err("Campanha")

    if device_id:
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Dispositivo não encontrado")
        if device.tenant_id and str(device.tenant_id) != tenant_id:
            raise _err("Dispositivo")


# ─── Spots CRUD ───────────────────────────────────────────────────────────────

@router.get("/", response_model=List[AudioSpotResponse])
def list_audio_spots(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    status: Optional[AudioSpotStatusEnum] = Query(None),
    tenant_id: Optional[str] = Query(None),
):
    query = db.query(AudioSpot)

    effective_tid = _effective_tenant_id(current_user, tenant_id)
    if effective_tid:
        query = query.filter(AudioSpot.tenant_id == effective_tid)

    if status:
        query = query.filter(AudioSpot.status == status)

    if search:
        query = query.filter(
            AudioSpot.name.ilike(f"%{search}%") | AudioSpot.description.ilike(f"%{search}%")
        )

    return query.offset(skip).limit(limit).all()


@router.get("/schedules", response_model=List[AudioSpotScheduleResponse])
def list_spot_schedules_by_scope(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    campaign_id: Optional[str] = Query(None),
    device_id: Optional[str] = Query(None),
    playlist_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Lista spot schedules filtrando por campaign_id, device_id ou playlist_id."""
    from core.models import AudioSpotSchedule

    tenant_id = _effective_tenant_id(current_user)
    query = db.query(AudioSpotSchedule)

    if tenant_id:
        query = query.filter(AudioSpotSchedule.tenant_id == tenant_id)

    if campaign_id:
        query = query.filter(AudioSpotSchedule.campaign_id == campaign_id)
    if device_id:
        query = query.filter(AudioSpotSchedule.device_id == device_id)
    if playlist_id:
        query = query.filter(AudioSpotSchedule.playlist_id == playlist_id)

    return query.order_by(AudioSpotSchedule.priority.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=AudioSpotResponse, status_code=http_status.HTTP_201_CREATED)
def create_audio_spot(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payload: AudioSpotCreate,
):
    _ensure_track_in_spot_scope(db, track_id=payload.track_id, current_user=current_user)

    obj_in = AudioSpotCreate(
        name=payload.name,
        description=payload.description,
        track_id=payload.track_id,
        status=payload.status,
        insertion_policy=payload.insertion_policy,
        tenant_id=_effective_tenant_id(current_user, payload.tenant_id),
    )
    return crud_audio_spot.create(db, obj_in=obj_in)


@router.get("/{spot_id}", response_model=AudioSpotResponse)
def get_audio_spot(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    spot_id: str,
):
    return _authorize_spot_access(db, spot_id=spot_id, current_user=current_user)


@router.put("/{spot_id}", response_model=AudioSpotResponse)
def update_audio_spot(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    spot_id: str,
    payload: AudioSpotUpdate,
):
    spot = _authorize_spot_access(db, spot_id=spot_id, current_user=current_user)
    if payload.track_id:
        _ensure_track_in_spot_scope(db, track_id=payload.track_id, current_user=current_user)
    return crud_audio_spot.update(db, db_obj=spot, obj_in=payload)


@router.delete("/{spot_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_audio_spot(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    spot_id: str,
):
    _authorize_spot_access(db, spot_id=spot_id, current_user=current_user)
    crud_audio_spot.remove(db, id=spot_id)


# ─── Spot Schedules por Playlist ──────────────────────────────────────────────

@router.get("/playlists/{playlist_id}/spot-schedules", response_model=List[AudioSpotScheduleResponse])
def list_playlist_spot_schedules(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Playlist não encontrada")
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, detail="Sem permissão para acessar esta playlist")

    schedules = crud_audio_spot_schedule.get_by_playlist(db, playlist_id=playlist_id)
    return schedules[skip: skip + limit]


@router.post(
    "/playlists/{playlist_id}/spot-schedules",
    response_model=AudioSpotScheduleResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_playlist_spot_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    payload: AudioSpotScheduleCreate,
):
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Playlist não encontrada")
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, detail="Sem permissão para acessar esta playlist")

    tenant_id = _effective_tenant_id(current_user)

    _validate_cross_tenant(
        db,
        tenant_id=tenant_id,
        playlist_id=playlist_id,
        campaign_id=payload.campaign_id,
        device_id=payload.device_id,
        spot_id=payload.spot_id,
    )

    _authorize_spot_access(db, spot_id=payload.spot_id, current_user=current_user)

    schedule = crud_audio_spot_schedule.create(
        db,
        obj_in=payload,
        playlist_id=playlist_id,
        tenant_id=tenant_id,
    )

    _invalidate_device_playlist_cache(_device_ids_for_playlist(db, playlist_id=playlist_id))

    log.info(
        "spot_schedule.created",
        extra={
            "tenant_id": tenant_id,
            "schedule_id": str(schedule.id),
            "spot_id": str(schedule.spot_id),
            "playlist_id": playlist_id,
            "interval_seconds": schedule.interval_seconds,
        },
    )
    return schedule


@router.get("/playlists/{playlist_id}/spot-schedules/{schedule_id}", response_model=AudioSpotScheduleResponse)
def get_playlist_spot_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    schedule_id: str,
):
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Playlist não encontrada")
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, detail="Sem permissão para acessar esta playlist")

    schedule = crud_audio_spot_schedule.get(db, id=schedule_id)
    if not schedule:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado")
    if str(schedule.playlist_id) != str(playlist_id):
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Agendamento não pertence a esta playlist")
    return schedule


@router.put("/playlists/{playlist_id}/spot-schedules/{schedule_id}", response_model=AudioSpotScheduleResponse)
def update_playlist_spot_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    schedule_id: str,
    payload: AudioSpotScheduleUpdate,
):
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Playlist não encontrada")
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, detail="Sem permissão para acessar esta playlist")

    schedule = crud_audio_spot_schedule.get(db, id=schedule_id)
    if not schedule:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado")
    if str(schedule.playlist_id) != str(playlist_id):
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Agendamento não pertence a esta playlist")

    tenant_id = _effective_tenant_id(current_user)
    _validate_cross_tenant(
        db,
        tenant_id=tenant_id,
        playlist_id=payload.playlist_id,
        campaign_id=payload.campaign_id,
        device_id=payload.device_id,
        spot_id=payload.spot_id,
    )

    if payload.spot_id:
        _authorize_spot_access(db, spot_id=payload.spot_id, current_user=current_user)

    updated = crud_audio_spot_schedule.update(db, db_obj=schedule, obj_in=payload)
    _invalidate_device_playlist_cache(_device_ids_for_playlist(db, playlist_id=playlist_id))

    log.info("spot_schedule.updated", extra={"schedule_id": schedule_id, "tenant_id": tenant_id})
    return updated


@router.delete("/playlists/{playlist_id}/spot-schedules/{schedule_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_playlist_spot_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    schedule_id: str,
):
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Playlist não encontrada")
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(http_status.HTTP_403_FORBIDDEN, detail="Sem permissão para acessar esta playlist")

    schedule = crud_audio_spot_schedule.get(db, id=schedule_id)
    if not schedule:
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado")
    if str(schedule.playlist_id) != str(playlist_id):
        raise HTTPException(http_status.HTTP_404_NOT_FOUND, detail="Agendamento não pertence a esta playlist")

    crud_audio_spot_schedule.remove(db, id=schedule_id)
    _invalidate_device_playlist_cache(_device_ids_for_playlist(db, playlist_id=playlist_id))

    log.info("spot_schedule.deleted", extra={"schedule_id": schedule_id, "playlist_id": playlist_id})
