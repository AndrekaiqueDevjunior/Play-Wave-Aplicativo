from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.dependencies import get_current_user
from core.models import AudioSpot, AudioTrack, User
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


def _invalidate_device_playlist_cache(device_ids: Optional[set[str]] = None) -> None:
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
        print(f"[audio-spots] Redis cache invalidation error: {exc}")


def _device_ids_for_playlist(db: Session, *, playlist_id: str) -> set[str]:
    from core.models import Device, Campaign

    device_ids = {
        str(row.id)
        for row in db.query(Device.id).filter(Device.audio_playlist_id == playlist_id).all()
    }
    campaigns = db.query(Campaign).filter(Campaign.audio_playlist_id == playlist_id).all()
    for campaign in campaigns:
        device_ids.update(str(device_id) for device_id in (campaign.device_ids or []) if device_id)
        rows = db.query(Device.id).filter(Device.current_campaign_id == campaign.id).all()
        device_ids.update(str(row.id) for row in rows)
    return device_ids


def _authorize_spot_access(
    db: Session, *, spot_id: str, current_user: User
) -> AudioSpot:
    spot = crud_audio_spot.get(db, id=spot_id)
    if not spot:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Spot de áudio não encontrado",
        )
    if current_user.role != "admin" and str(spot.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar este spot",
        )
    return spot


def _ensure_track_in_spot_scope(
    db: Session, *, track_id: str, current_user: User
) -> AudioTrack:
    track = db.query(AudioTrack).filter(AudioTrack.id == track_id).first()
    if not track:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Faixa de áudio não encontrada",
        )
    if current_user.role != "admin" and str(track.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para usar esta faixa",
        )
    return track


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
    """Lista spots de áudio"""
    query = db.query(AudioSpot)

    effective_tenant_id = tenant_id
    if current_user.role != "admin":
        effective_tenant_id = str(current_user.tenant_id)

    if effective_tenant_id:
        query = query.filter(AudioSpot.tenant_id == effective_tenant_id)

    if status:
        query = query.filter(AudioSpot.status == status)

    if search:
        query = query.filter(
            AudioSpot.name.ilike(f"%{search}%") | AudioSpot.description.ilike(f"%{search}%")
        )

    total = query.count()
    spots = query.offset(skip).limit(limit).all()

    return spots


@router.post("/", response_model=AudioSpotResponse, status_code=http_status.HTTP_201_CREATED)
def create_audio_spot(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    payload: AudioSpotCreate,
):
    """Cria novo spot de áudio"""
    track = _ensure_track_in_spot_scope(db, track_id=payload.track_id, current_user=current_user)

    obj_in = AudioSpotCreate(
        name=payload.name,
        description=payload.description,
        track_id=payload.track_id,
        status=payload.status,
        insertion_policy=payload.insertion_policy,
        tenant_id=payload.tenant_id or (str(current_user.tenant_id) if current_user.role != "admin" else None),
    )

    spot = crud_audio_spot.create(db, obj_in=obj_in)
    return spot


@router.get("/{spot_id}", response_model=AudioSpotResponse)
def get_audio_spot(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    spot_id: str,
):
    """Obtém um spot específico"""
    spot = _authorize_spot_access(db, spot_id=spot_id, current_user=current_user)
    return spot


@router.put("/{spot_id}", response_model=AudioSpotResponse)
def update_audio_spot(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    spot_id: str,
    payload: AudioSpotUpdate,
):
    """Atualiza um spot de áudio"""
    spot = _authorize_spot_access(db, spot_id=spot_id, current_user=current_user)

    if payload.track_id:
        _ensure_track_in_spot_scope(db, track_id=payload.track_id, current_user=current_user)

    spot = crud_audio_spot.update(db, db_obj=spot, obj_in=payload)
    return spot


@router.delete("/{spot_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def delete_audio_spot(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    spot_id: str,
):
    """Deleta um spot de áudio"""
    spot = _authorize_spot_access(db, spot_id=spot_id, current_user=current_user)
    crud_audio_spot.remove(db, id=spot_id)


# ─── Spot Schedules ──────────────────────────────────────────────────────────


@router.get(
    "/playlists/{playlist_id}/spot-schedules",
    response_model=List[AudioSpotScheduleResponse],
)
def list_playlist_spot_schedules(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Lista agendamentos de spots para uma playlist"""
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Playlist não encontrada",
        )
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta playlist",
        )

    schedules = crud_audio_spot_schedule.get_by_playlist(db, playlist_id=playlist_id)
    return schedules[skip : skip + limit]


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
    """Cria novo agendamento de spot"""
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Playlist não encontrada",
        )
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta playlist",
        )

    spot = _authorize_spot_access(db, spot_id=payload.spot_id, current_user=current_user)

    obj_in = AudioSpotScheduleCreate(
        spot_id=payload.spot_id,
        interval_seconds=payload.interval_seconds,
        start_time=payload.start_time,
        end_time=payload.end_time,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        priority=payload.priority,
        is_active=payload.is_active,
    )

    schedule = crud_audio_spot_schedule.create(
        db, obj_in=obj_in, playlist_id=playlist_id
    )
    _invalidate_device_playlist_cache(_device_ids_for_playlist(db, playlist_id=playlist_id))

    return schedule


@router.get(
    "/playlists/{playlist_id}/spot-schedules/{schedule_id}",
    response_model=AudioSpotScheduleResponse,
)
def get_playlist_spot_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    schedule_id: str,
):
    """Obtém um agendamento específico de spot"""
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Playlist não encontrada",
        )
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta playlist",
        )

    schedule = crud_audio_spot_schedule.get(db, id=schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Agendamento não encontrado",
        )
    if str(schedule.playlist_id) != str(playlist_id):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Agendamento não pertence a esta playlist",
        )

    return schedule


@router.put(
    "/playlists/{playlist_id}/spot-schedules/{schedule_id}",
    response_model=AudioSpotScheduleResponse,
)
def update_playlist_spot_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    schedule_id: str,
    payload: AudioSpotScheduleUpdate,
):
    """Atualiza um agendamento de spot"""
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Playlist não encontrada",
        )
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta playlist",
        )

    schedule = crud_audio_spot_schedule.get(db, id=schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Agendamento não encontrado",
        )
    if str(schedule.playlist_id) != str(playlist_id):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Agendamento não pertence a esta playlist",
        )

    if payload.spot_id:
        _authorize_spot_access(db, spot_id=payload.spot_id, current_user=current_user)

    schedule = crud_audio_spot_schedule.update(db, db_obj=schedule, obj_in=payload)
    _invalidate_device_playlist_cache(_device_ids_for_playlist(db, playlist_id=playlist_id))

    return schedule


@router.delete(
    "/playlists/{playlist_id}/spot-schedules/{schedule_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
def delete_playlist_spot_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    schedule_id: str,
):
    """Deleta um agendamento de spot"""
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Playlist não encontrada",
        )
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta playlist",
        )

    schedule = crud_audio_spot_schedule.get(db, id=schedule_id)
    if not schedule:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Agendamento não encontrado",
        )
    if str(schedule.playlist_id) != str(playlist_id):
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Agendamento não pertence a esta playlist",
        )

    crud_audio_spot_schedule.remove(db, id=schedule_id)
    _invalidate_device_playlist_cache(_device_ids_for_playlist(db, playlist_id=playlist_id))
