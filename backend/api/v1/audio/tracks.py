from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import os
import shutil
from datetime import datetime

from core.database import get_db
from core.dependencies import get_current_user
from core.models import User
from core.schemas_completos import (
    AudioTrackCreate, AudioTrackUpdate, AudioTrackResponse, 
    AudioTrackCategoryEnum, AudioTrackStatusEnum
)
from crud.entidades import crud_audio_track
from core.config import settings

router = APIRouter(prefix="/audio/tracks", tags=["audio-tracks"])


@router.get("/", response_model=List[AudioTrackResponse])
def get_audio_tracks(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    category: Optional[AudioTrackCategoryEnum] = Query(None),
    status: Optional[AudioTrackStatusEnum] = Query(None),
    tenant_id: Optional[str] = Query(None)
):
    """
    Lista faixas de áudio com filtros opcionais
    """
    # Se não for admin, filtra apenas do tenant do usuário
    if current_user.role != "admin" and not tenant_id:
        tenant_id = str(current_user.tenant_id)
    
    # Aplicar filtros específicos
    if category:
        tracks = crud_audio_track.get_by_category(db, category=category)
    elif status:
        tracks = crud_audio_track.get_by_status(db, status=status)
    elif tenant_id:
        tracks = crud_audio_track.get_by_tenant(db, tenant_id=tenant_id)
    elif search:
        tracks = crud_audio_track.search(db, query=search, skip=skip, limit=limit)
    else:
        tracks = crud_audio_track.get_multi(db, skip=skip, limit=limit)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        tracks = [t for t in tracks if str(t.tenant_id) == str(current_user.tenant_id)]
    
    return tracks


@router.get("/{track_id}", response_model=AudioTrackResponse)
def get_audio_track(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    track_id: str
):
    """
    Obtém faixa de áudio por ID
    """
    track = crud_audio_track.get(db, id=track_id)
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faixa de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(track.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta faixa"
        )
    
    return track


@router.post("/", response_model=AudioTrackResponse)
def create_audio_track(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    track_in: AudioTrackCreate
):
    """
    Cria nova faixa de áudio
    """
    # Atribuir tenant se não for admin
    if current_user.role != "admin":
        track_in.tenant_id = current_user.tenant_id
    
    track = crud_audio_track.create(db, obj_in=track_in)
    return track


@router.post("/upload", response_model=AudioTrackResponse)
def upload_audio_track(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
    name: str = Query(...),
    category: Optional[AudioTrackCategoryEnum] = Query(AudioTrackCategoryEnum.MUSIC),
    description: Optional[str] = Query(None)
):
    """
    Faz upload de arquivo de áudio
    """
    # Validar tipo de arquivo
    allowed_types = [
        "audio/mp3", "audio/wav", "audio/ogg", 
        "audio/m4a", "audio/mp4", "audio/aac"
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo não permitido: {file.content_type}"
        )
    
    # Criar diretório de uploads se não existir
    upload_dir = "uploads/audio/tracks"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Gerar nome de arquivo único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    # Salvar arquivo
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar arquivo: {str(e)}"
        )
    
    # Criar faixa no banco
    track_data = {
        "name": name,
        "description": description,
        "file_url": f"/uploads/audio/tracks/{filename}",
        "mime_type": file.content_type,
        "file_size": os.path.getsize(file_path),
        "category": category
    }
    
    if current_user.role != "admin":
        track_data["tenant_id"] = current_user.tenant_id
    
    track = crud_audio_track.create(db, obj_in=AudioTrackCreate(**track_data))
    return track


@router.put("/{track_id}", response_model=AudioTrackResponse)
def update_audio_track(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    track_id: str,
    track_in: AudioTrackUpdate
):
    """
    Atualiza faixa de áudio
    """
    track = crud_audio_track.get(db, id=track_id)
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faixa de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(track.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta faixa"
        )
    
    track = crud_audio_track.update(db, db_obj=track, obj_in=track_in)
    return track


@router.delete("/{track_id}")
def delete_audio_track(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    track_id: str
):
    """
    Remove faixa de áudio
    """
    track = crud_audio_track.get(db, id=track_id)
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faixa de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(track.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para remover esta faixa"
        )
    
    # Remover arquivo físico se existir
    if track.file_url and track.file_url.startswith("/uploads/"):
        file_path = track.file_url[1:]  # Remove o /
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass  # Ignora erro ao remover arquivo
    
    crud_audio_track.remove(db, id=track_id)
    return {"message": "Faixa de áudio removida com sucesso"}


@router.patch("/{track_id}/status")
def update_track_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    track_id: str,
    status: AudioTrackStatusEnum
):
    """
    Atualiza status da faixa de áudio
    """
    track = crud_audio_track.get(db, id=track_id)
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faixa de áudio não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(track.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta faixa"
        )
    
    track = crud_audio_track.update_status(db, db_obj=track, status=status)
    return {"message": f"Status atualizado para {status}"}


@router.get("/statistics/overview")
def get_audio_track_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém estatísticas das faixas de áudio
    """
    # Se não for admin, filtra apenas do tenant do usuário
    tenant_id = None if current_user.role == "admin" else str(current_user.tenant_id)
    
    statistics = crud_audio_track.get_statistics(db, tenant_id=tenant_id)
    return statistics


@router.get("/active/list", response_model=List[AudioTrackResponse])
def get_active_tracks(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista faixas de áudio ativas
    """
    tracks = crud_audio_track.get_active(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        tracks = [t for t in tracks if str(t.tenant_id) == str(current_user.tenant_id)]
    
    return tracks[skip:skip+limit]


@router.get("/by-category/{category}", response_model=List[AudioTrackResponse])
def get_tracks_by_category(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category: AudioTrackCategoryEnum,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista faixas por categoria
    """
    tracks = crud_audio_track.get_by_category(db, category=category)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        tracks = [t for t in tracks if str(t.tenant_id) == str(current_user.tenant_id)]
    
    return tracks[skip:skip+limit]


@router.get("/by-duration", response_model=List[AudioTrackResponse])
def get_tracks_by_duration(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    min_seconds: Optional[int] = Query(None, ge=0),
    max_seconds: Optional[int] = Query(None, ge=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista faixas por faixa de duração
    """
    tracks = crud_audio_track.get_by_duration_range(db, min_seconds=min_seconds, max_seconds=max_seconds)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        tracks = [t for t in tracks if str(t.tenant_id) == str(current_user.tenant_id)]
    
    return tracks[skip:skip+limit]
