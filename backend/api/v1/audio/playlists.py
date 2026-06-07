from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from uuid import UUID

from core.database import get_db
from core.dependencies import get_current_user
from core.models import AudioPlaylistItem, AudioTrack, Campaign, Device, User, AudioFolder
from core.schemas_completos import (
    AudioPlaylistCreate,
    AudioPlaylistItemBulkCreate,
    AudioPlaylistItemReorderPayload,
    AudioPlaylistItemResponse,
    AudioPlaylistItemUpdate,
    AudioPlaylistResponse,
    AudioPlaylistStatusEnum,
    AudioPlaylistUpdate,
    AudioPlaylistFolderScheduleCreate,
    AudioPlaylistFolderScheduleResponse,
    AudioPlaylistFolderScheduleUpdate,
)
from crud.entidades import crud_audio_playlist, crud_audio_playlist_item, crud_audio_playlist_folder_schedule

router = APIRouter(prefix="/audio/playlists", tags=["audio-playlists"])


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
        print(f"[audio-playlists] Redis cache invalidation error: {exc}")


import logging
_log = logging.getLogger("playwave.audio_playlists")


def _publish_playlist_invalidated(device_ids: set[str], *, reason: str) -> None:
    """Push SSE para todos os devices afetados por mudança de playlist/faixa."""
    if not device_ids:
        return
    try:
        from services.event_bus import publish_device_event
        for did in device_ids:
            publish_device_event(did, event_type="playlist_invalidated", data={"reason": reason})
    except Exception as exc:
        _log.warning("playlist publish event error: %s", exc)


def _device_ids_for_playlist(db: Session, *, playlist_id: str) -> set[str]:
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


def _authorize_playlist_access(
    db: Session, *, playlist_id: str, current_user: User
):
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada",
        )
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta playlist",
        )
    return playlist


def _ensure_track_in_playlist_scope(
    db: Session, *, track_id: str, playlist, current_user: User
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
    if playlist.tenant_id and track.tenant_id and str(track.tenant_id) != str(playlist.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Faixa pertence a outro tenant",
        )
    return track


def _sync_legacy_track_fields(db: Session, *, playlist) -> None:
    """Mirror active relational items into legacy track_ids/track_volumes JSON."""
    items = crud_audio_playlist_item.list_by_playlist(db, playlist_id=str(playlist.id))
    active_items = [item for item in items if item.is_active]
    playlist.track_ids = [str(item.track_id) for item in active_items]
    playlist.track_volumes = {
        str(item.track_id): item.volume_override
        for item in active_items
        if item.volume_override is not None
    }
    db.add(playlist)


def _replace_items_from_legacy_fields(
    db: Session,
    *,
    playlist,
    current_user: User,
    track_ids: Optional[List[str]],
    track_volumes: Optional[Dict[str, float]],
) -> None:
    for item in crud_audio_playlist_item.list_by_playlist(db, playlist_id=str(playlist.id)):
        db.delete(item)
    db.flush()

    volumes = track_volumes or {}
    for index, track_id in enumerate(track_ids or []):
        track = _ensure_track_in_playlist_scope(
            db, track_id=str(track_id), playlist=playlist, current_user=current_user
        )
        db.add(
            AudioPlaylistItem(
                playlist_id=playlist.id,
                track_id=track.id,
                order_index=index * 10,
                volume_override=volumes.get(str(track_id)),
                is_active=True,
            )
        )
    db.flush()
    crud_audio_playlist_item.compact_order(db, playlist_id=str(playlist.id))
    _sync_legacy_track_fields(db, playlist=playlist)


@router.get("/", response_model=List[AudioPlaylistResponse])
def get_audio_playlists(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    status: Optional[AudioPlaylistStatusEnum] = Query(None),
    category_id: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None)
):
    """
    Lista playlists de áudio com filtros opcionais
    """
    # Se não for admin, filtra apenas do tenant do usuário
    if current_user.role != "admin" and not tenant_id:
        tenant_id = str(current_user.tenant_id)

    # Aplicar filtros específicos
    if status:
        playlists = crud_audio_playlist.get_by_status(db, status=status)
    elif tenant_id:
        playlists = crud_audio_playlist.get_by_tenant(db, tenant_id=tenant_id)
    elif search:
        playlists = crud_audio_playlist.search(db, query=search, skip=skip, limit=limit)
    else:
        playlists = crud_audio_playlist.get_multi(db, skip=skip, limit=limit)

    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        playlists = [p for p in playlists if str(p.tenant_id) == str(current_user.tenant_id)]

    if category_id:
        playlists = [p for p in playlists if str(p.category_id) == str(category_id)]

    return playlists


@router.get("/{playlist_id}", response_model=AudioPlaylistResponse)
def get_audio_playlist(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str
):
    """
    Obtém playlist de áudio por ID
    """
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta playlist"
        )
    
    return playlist


@router.get("/{playlist_id}/with-tracks", response_model=AudioPlaylistResponse)
def get_audio_playlist_with_tracks(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str
):
    """
    Obtém playlist de áudio com faixas carregadas
    """
    playlist = crud_audio_playlist.get_with_tracks(db, playlist_id=playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta playlist"
        )
    
    return playlist


@router.get("/{playlist_id}/items", response_model=List[AudioPlaylistItemResponse])
def list_audio_playlist_items(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
):
    playlist = _authorize_playlist_access(
        db, playlist_id=playlist_id, current_user=current_user
    )
    return crud_audio_playlist_item.list_by_playlist(
        db, playlist_id=str(playlist.id)
    )


@router.post(
    "/{playlist_id}/items",
    response_model=List[AudioPlaylistItemResponse],
    status_code=http_status.HTTP_201_CREATED,
)
def add_audio_playlist_items(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    payload: AudioPlaylistItemBulkCreate,
):
    playlist = _authorize_playlist_access(
        db, playlist_id=playlist_id, current_user=current_user
    )
    affected_device_ids = _device_ids_for_playlist(db, playlist_id=playlist_id)
    next_index = crud_audio_playlist_item.next_order_index(
        db, playlist_id=str(playlist.id)
    )

    for entry in payload.items:
        track = _ensure_track_in_playlist_scope(
            db,
            track_id=entry.track_id,
            playlist=playlist,
            current_user=current_user,
        )
        order_index = entry.order_index if entry.order_index is not None else next_index
        if entry.order_index is None:
            next_index += 10
        db.add(
            AudioPlaylistItem(
                playlist_id=playlist.id,
                track_id=track.id,
                order_index=order_index,
                volume_override=entry.volume_override,
                is_active=entry.is_active if entry.is_active is not None else True,
            )
        )

    db.flush()
    crud_audio_playlist_item.compact_order(db, playlist_id=str(playlist.id))
    _sync_legacy_track_fields(db, playlist=playlist)
    db.commit()
    _invalidate_device_playlist_cache(affected_device_ids)
    _publish_playlist_invalidated(affected_device_ids, reason="playlist.changed")
    return crud_audio_playlist_item.list_by_playlist(
        db, playlist_id=str(playlist.id)
    )


@router.put(
    "/{playlist_id}/items/{item_id}",
    response_model=AudioPlaylistItemResponse,
)
def update_audio_playlist_item(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    item_id: str,
    payload: AudioPlaylistItemUpdate,
):
    playlist = _authorize_playlist_access(
        db, playlist_id=playlist_id, current_user=current_user
    )
    item = crud_audio_playlist_item.get(db, item_id=item_id)
    if not item or str(item.playlist_id) != str(playlist.id):
        raise HTTPException(status_code=404, detail="Item de playlist não encontrado")

    data = payload.model_dump(exclude_unset=True)
    if "track_id" in data and data["track_id"]:
        track = _ensure_track_in_playlist_scope(
            db,
            track_id=data["track_id"],
            playlist=playlist,
            current_user=current_user,
        )
        data["track_id"] = track.id

    affected_device_ids = _device_ids_for_playlist(db, playlist_id=playlist_id)
    for field, value in data.items():
        setattr(item, field, value)
    db.add(item)
    db.flush()
    if "order_index" in data:
        crud_audio_playlist_item.compact_order(db, playlist_id=str(playlist.id))
    _sync_legacy_track_fields(db, playlist=playlist)
    db.commit()
    db.refresh(item)
    _invalidate_device_playlist_cache(affected_device_ids)
    _publish_playlist_invalidated(affected_device_ids, reason="playlist.changed")
    return item


@router.delete("/{playlist_id}/items/{item_id}", status_code=http_status.HTTP_204_NO_CONTENT)
def remove_audio_playlist_item(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    item_id: str,
):
    playlist = _authorize_playlist_access(
        db, playlist_id=playlist_id, current_user=current_user
    )
    item = crud_audio_playlist_item.get(db, item_id=item_id)
    if not item or str(item.playlist_id) != str(playlist.id):
        raise HTTPException(status_code=404, detail="Item de playlist não encontrado")

    affected_device_ids = _device_ids_for_playlist(db, playlist_id=playlist_id)
    db.delete(item)
    db.flush()
    crud_audio_playlist_item.compact_order(db, playlist_id=str(playlist.id))
    _sync_legacy_track_fields(db, playlist=playlist)
    db.commit()
    _invalidate_device_playlist_cache(affected_device_ids)
    _publish_playlist_invalidated(affected_device_ids, reason="playlist.changed")
    return None


@router.patch(
    "/{playlist_id}/items/reorder",
    response_model=List[AudioPlaylistItemResponse],
)
def reorder_audio_playlist_items(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    payload: AudioPlaylistItemReorderPayload,
):
    playlist = _authorize_playlist_access(
        db, playlist_id=playlist_id, current_user=current_user
    )
    affected_device_ids = _device_ids_for_playlist(db, playlist_id=playlist_id)
    items = crud_audio_playlist_item.apply_reorder(
        db,
        playlist_id=str(playlist.id),
        entries=[
            {"item_id": entry.item_id, "order_index": entry.order_index}
            for entry in payload.items
        ],
    )
    _sync_legacy_track_fields(db, playlist=playlist)
    db.commit()
    _invalidate_device_playlist_cache(affected_device_ids)
    _publish_playlist_invalidated(affected_device_ids, reason="playlist.changed")
    return items


@router.post("/", response_model=AudioPlaylistResponse)
def create_audio_playlist(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_in: AudioPlaylistCreate
):
    """
    Cria nova playlist de áudio
    """
    # Atribuir tenant se não for admin
    if current_user.role != "admin":
        playlist_in.tenant_id = str(current_user.tenant_id)
    
    playlist = crud_audio_playlist.create(db, obj_in=playlist_in)
    if playlist.track_ids:
        affected_device_ids = _device_ids_for_playlist(db, playlist_id=str(playlist.id))
        _replace_items_from_legacy_fields(
            db,
            playlist=playlist,
            current_user=current_user,
            track_ids=playlist.track_ids,
            track_volumes=playlist.track_volumes,
        )
        db.commit()
        db.refresh(playlist)
        _invalidate_device_playlist_cache(affected_device_ids)
    _publish_playlist_invalidated(affected_device_ids, reason="playlist.changed")
    return playlist


@router.put("/{playlist_id}", response_model=AudioPlaylistResponse)
def update_audio_playlist(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    playlist_in: AudioPlaylistUpdate
):
    """
    Atualiza playlist de áudio
    """
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta playlist"
        )
    
    affected_device_ids = _device_ids_for_playlist(db, playlist_id=playlist_id)
    data = playlist_in.model_dump(exclude_unset=True)
    playlist = crud_audio_playlist.update(db, db_obj=playlist, obj_in=playlist_in)
    if "track_ids" in data or "track_volumes" in data:
        _replace_items_from_legacy_fields(
            db,
            playlist=playlist,
            current_user=current_user,
            track_ids=playlist.track_ids,
            track_volumes=playlist.track_volumes,
        )
        db.commit()
        db.refresh(playlist)
    _invalidate_device_playlist_cache(affected_device_ids)
    _publish_playlist_invalidated(affected_device_ids, reason="playlist.changed")
    return playlist


@router.delete("/{playlist_id}")
def delete_audio_playlist(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str
):
    """
    Remove playlist de áudio
    """
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para remover esta playlist"
        )
    
    affected_device_ids = _device_ids_for_playlist(db, playlist_id=playlist_id)
    crud_audio_playlist.remove(db, id=playlist_id)
    _invalidate_device_playlist_cache(affected_device_ids)
    _publish_playlist_invalidated(affected_device_ids, reason="playlist.changed")
    return {"message": "Playlist de áudio removida com sucesso"}


@router.patch("/{playlist_id}/status")
def update_playlist_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    status: AudioPlaylistStatusEnum
):
    """
    Atualiza status da playlist de áudio
    """
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta playlist"
        )
    
    affected_device_ids = _device_ids_for_playlist(db, playlist_id=playlist_id)
    playlist = crud_audio_playlist.update_status(db, db_obj=playlist, status=status)
    _invalidate_device_playlist_cache(affected_device_ids)
    _publish_playlist_invalidated(affected_device_ids, reason="playlist.changed")
    return {"message": f"Status atualizado para {status}"}


@router.post("/{playlist_id}/tracks/{track_id}")
def add_track_to_playlist(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    track_id: str,
    volume: Optional[float] = Query(None, ge=0.0, le=1.0)
):
    """
    Adiciona faixa à playlist
    """
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para modificar esta playlist"
        )
    
    affected_device_ids = _device_ids_for_playlist(db, playlist_id=playlist_id)
    playlist = crud_audio_playlist.add_track(db, playlist_id=playlist_id, track_id=track_id, volume=volume)
    _replace_items_from_legacy_fields(
        db,
        playlist=playlist,
        current_user=current_user,
        track_ids=playlist.track_ids,
        track_volumes=playlist.track_volumes,
    )
    db.commit()
    db.refresh(playlist)
    _invalidate_device_playlist_cache(affected_device_ids)
    _publish_playlist_invalidated(affected_device_ids, reason="playlist.changed")
    return {"message": "Faixa adicionada à playlist com sucesso"}


@router.delete("/{playlist_id}/tracks/{track_id}")
def remove_track_from_playlist(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    track_id: str
):
    """
    Remove faixa da playlist
    """
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para modificar esta playlist"
        )
    
    affected_device_ids = _device_ids_for_playlist(db, playlist_id=playlist_id)
    playlist = crud_audio_playlist.remove_track(db, playlist_id=playlist_id, track_id=track_id)
    _replace_items_from_legacy_fields(
        db,
        playlist=playlist,
        current_user=current_user,
        track_ids=playlist.track_ids,
        track_volumes=playlist.track_volumes,
    )
    db.commit()
    db.refresh(playlist)
    _invalidate_device_playlist_cache(affected_device_ids)
    _publish_playlist_invalidated(affected_device_ids, reason="playlist.changed")
    return {"message": "Faixa removida da playlist com sucesso"}


@router.put("/{playlist_id}/tracks/reorder")
def reorder_playlist_tracks(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    track_ids: List[str]
):
    """
    Reordena faixas da playlist
    """
    playlist = crud_audio_playlist.get(db, id=playlist_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para modificar esta playlist"
        )
    
    affected_device_ids = _device_ids_for_playlist(db, playlist_id=playlist_id)
    playlist = crud_audio_playlist.reorder_tracks(db, playlist_id=playlist_id, track_ids=track_ids)
    _replace_items_from_legacy_fields(
        db,
        playlist=playlist,
        current_user=current_user,
        track_ids=playlist.track_ids,
        track_volumes=playlist.track_volumes,
    )
    db.commit()
    db.refresh(playlist)
    _invalidate_device_playlist_cache(affected_device_ids)
    _publish_playlist_invalidated(affected_device_ids, reason="playlist.changed")
    return {"message": "Faixas reordenadas com sucesso"}


@router.get("/statistics/overview")
def get_audio_playlist_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém estatísticas das playlists de áudio
    """
    # Se não for admin, filtra apenas do tenant do usuário
    tenant_id = None if current_user.role == "admin" else str(current_user.tenant_id)
    
    statistics = crud_audio_playlist.get_statistics(db, tenant_id=tenant_id)
    return statistics


@router.get("/active/list", response_model=List[AudioPlaylistResponse])
def get_active_playlists(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista playlists de áudio ativas
    """
    playlists = crud_audio_playlist.get_active(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        playlists = [p for p in playlists if str(p.tenant_id) == str(current_user.tenant_id)]
    
    return playlists[skip:skip+limit]


@router.get("/by-device/{device_id}", response_model=AudioPlaylistResponse)
def get_playlist_by_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str
):
    """
    Obtém playlist associada a um dispositivo
    """
    playlist = crud_audio_playlist.get_by_device(db, device_id=device_id)
    if not playlist:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Nenhuma playlist encontrada para este dispositivo"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta playlist"
        )
    
    return playlist


# ─── Playlist Folder Schedules ──────────────────────────────────────────────────


@router.get(
    "/{playlist_id}/folder-schedules",
    response_model=List[AudioPlaylistFolderScheduleResponse],
)
def list_playlist_folder_schedules(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Lista agendamentos de pastas para uma playlist de áudio"""
    playlist = _authorize_playlist_access(db, playlist_id=playlist_id, current_user=current_user)

    schedules = crud_audio_playlist_folder_schedule.get_by_playlist(
        db, playlist_id=playlist_id
    )
    return schedules[skip : skip + limit]


@router.post(
    "/{playlist_id}/folder-schedules",
    response_model=AudioPlaylistFolderScheduleResponse,
    status_code=http_status.HTTP_201_CREATED,
)
def create_playlist_folder_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    payload: AudioPlaylistFolderScheduleCreate,
):
    """Cria novo agendamento de pasta para uma playlist"""
    playlist = _authorize_playlist_access(db, playlist_id=playlist_id, current_user=current_user)

    folder = db.query(AudioFolder).filter(AudioFolder.id == payload.folder_id).first()
    if not folder:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Pasta de áudio não encontrada",
        )
    if current_user.role != "admin" and str(folder.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para usar esta pasta",
        )

    obj_in = AudioPlaylistFolderScheduleCreate(
        folder_id=payload.folder_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        days_of_week=payload.days_of_week,
        priority=payload.priority,
        play_mode=payload.play_mode,
        is_active=payload.is_active,
    )

    schedule = crud_audio_playlist_folder_schedule.create(
        db, obj_in=obj_in, playlist_id=playlist_id
    )
    _affected = _device_ids_for_playlist(db, playlist_id=playlist_id)
    _invalidate_device_playlist_cache(_affected)
    _publish_playlist_invalidated(_affected, reason="playlist.changed")

    return schedule


@router.get(
    "/{playlist_id}/folder-schedules/{schedule_id}",
    response_model=AudioPlaylistFolderScheduleResponse,
)
def get_playlist_folder_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    schedule_id: str,
):
    """Obtém um agendamento específico de pasta"""
    playlist = _authorize_playlist_access(db, playlist_id=playlist_id, current_user=current_user)

    schedule = crud_audio_playlist_folder_schedule.get(db, id=schedule_id)
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
    "/{playlist_id}/folder-schedules/{schedule_id}",
    response_model=AudioPlaylistFolderScheduleResponse,
)
def update_playlist_folder_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    schedule_id: str,
    payload: AudioPlaylistFolderScheduleUpdate,
):
    """Atualiza um agendamento de pasta"""
    playlist = _authorize_playlist_access(db, playlist_id=playlist_id, current_user=current_user)

    schedule = crud_audio_playlist_folder_schedule.get(db, id=schedule_id)
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

    if payload.folder_id:
        folder = db.query(AudioFolder).filter(AudioFolder.id == payload.folder_id).first()
        if not folder:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Pasta de áudio não encontrada",
            )
        if current_user.role != "admin" and str(folder.tenant_id) != str(current_user.tenant_id):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para usar esta pasta",
            )

    schedule = crud_audio_playlist_folder_schedule.update(
        db, db_obj=schedule, obj_in=payload
    )
    _affected = _device_ids_for_playlist(db, playlist_id=playlist_id)
    _invalidate_device_playlist_cache(_affected)
    _publish_playlist_invalidated(_affected, reason="playlist.changed")

    return schedule


@router.delete(
    "/{playlist_id}/folder-schedules/{schedule_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
)
def delete_playlist_folder_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    playlist_id: str,
    schedule_id: str,
):
    """Deleta um agendamento de pasta"""
    playlist = _authorize_playlist_access(db, playlist_id=playlist_id, current_user=current_user)

    schedule = crud_audio_playlist_folder_schedule.get(db, id=schedule_id)
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

    crud_audio_playlist_folder_schedule.remove(db, id=schedule_id)
    _affected = _device_ids_for_playlist(db, playlist_id=playlist_id)
    _invalidate_device_playlist_cache(_affected)
    _publish_playlist_invalidated(_affected, reason="playlist.changed")
