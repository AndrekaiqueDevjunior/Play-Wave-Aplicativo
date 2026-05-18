from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from uuid import UUID

from core.database import get_db
from core.dependencies import get_current_user
from core.models import User
from core.schemas_completos import (
    AudioPlaylistCreate, AudioPlaylistUpdate, AudioPlaylistResponse, 
    AudioPlaylistStatusEnum
)
from crud.entidades import crud_audio_playlist

router = APIRouter(prefix="/audio/playlists", tags=["audio-playlists"])


def _invalidate_device_playlist_cache() -> None:
    from core.config import get_redis_client

    redis_client = get_redis_client()
    if not redis_client:
        return
    try:
        for key in redis_client.scan_iter("device_playlist:*"):
            redis_client.delete(key)
    except Exception as exc:
        print(f"[audio-playlists] Redis cache invalidation error: {exc}")


@router.get("/", response_model=List[AudioPlaylistResponse])
def get_audio_playlists(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    status: Optional[AudioPlaylistStatusEnum] = Query(None),
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta playlist"
        )
    
    return playlist


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
    _invalidate_device_playlist_cache()
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta playlist"
        )
    
    playlist = crud_audio_playlist.update(db, db_obj=playlist, obj_in=playlist_in)
    _invalidate_device_playlist_cache()
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para remover esta playlist"
        )
    
    crud_audio_playlist.remove(db, id=playlist_id)
    _invalidate_device_playlist_cache()
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta playlist"
        )
    
    playlist = crud_audio_playlist.update_status(db, db_obj=playlist, status=status)
    _invalidate_device_playlist_cache()
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para modificar esta playlist"
        )
    
    playlist = crud_audio_playlist.add_track(db, playlist_id=playlist_id, track_id=track_id, volume=volume)
    _invalidate_device_playlist_cache()
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para modificar esta playlist"
        )
    
    playlist = crud_audio_playlist.remove_track(db, playlist_id=playlist_id, track_id=track_id)
    _invalidate_device_playlist_cache()
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playlist de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para modificar esta playlist"
        )
    
    playlist = crud_audio_playlist.reorder_tracks(db, playlist_id=playlist_id, track_ids=track_ids)
    _invalidate_device_playlist_cache()
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma playlist encontrada para este dispositivo"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(playlist.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta playlist"
        )
    
    return playlist
