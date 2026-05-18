from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import re
import shutil
from datetime import datetime

from core.database import get_db
from core.dependencies import get_current_user
from core.models import AudioTrack, User
from core.schemas_completos import (
    AudioTrackCreate, AudioTrackUpdate, AudioTrackResponse, 
    AudioTrackCategoryEnum, AudioTrackStatusEnum
)
from crud.entidades import crud_audio_track

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
    query = db.query(AudioTrack)

    effective_tenant_id = tenant_id
    if current_user.role != "admin":
        effective_tenant_id = str(current_user.tenant_id)

    if effective_tenant_id:
        query = query.filter(AudioTrack.tenant_id == effective_tenant_id)
    if category:
        query = query.filter(AudioTrack.category == category.value)
    if status:
        query = query.filter(AudioTrack.status == status.value)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                AudioTrack.name.ilike(like),
                AudioTrack.description.ilike(like),
                cast(AudioTrack.category, String).ilike(like),
                AudioTrack.notes.ilike(like),
            )
        )

    return query.offset(skip).limit(limit).all()


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
    tracks = crud_audio_track.get_by_category(db, category=category.value)

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
        track_in.tenant_id = str(current_user.tenant_id)
    
    track = crud_audio_track.create(db, obj_in=track_in)
    return track


@router.post("/upload", response_model=AudioTrackResponse)
def upload_audio_track(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
    name: str = Form(...),
    category: Optional[AudioTrackCategoryEnum] = Form(AudioTrackCategoryEnum.MUSIC),
    track_status: Optional[AudioTrackStatusEnum] = Form(AudioTrackStatusEnum.ACTIVE, alias="status"),
    description: Optional[str] = Form(None),
    duration_seconds: Optional[int] = Form(None),
    notes: Optional[str] = Form(None)
):
    """
    Faz upload de arquivo de áudio
    """
    # Validar tipo de arquivo
    allowed_types = [
        "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
        "audio/wave", "audio/x-pn-wav", "audio/ogg", "audio/m4a",
        "audio/x-m4a", "audio/mp4", "audio/aac",
        "audio/opus", "audio/flac", "audio/x-flac", "audio/webm",
        "audio/x-opus", "audio/ogg; codecs=opus",
        "video/mpeg",
    ]
    allowed_extensions = {".mp3", ".wav", ".ogg", ".m4a", ".aac", ".opus", ".flac", ".weba", ".mpeg", ".mpg"}
    content_type = (file.content_type or "").lower()
    extension = os.path.splitext(file.filename or "")[1].lower()
    
    if content_type not in allowed_types and extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Tipo de arquivo não permitido. "
                f"MIME recebido: {content_type or 'desconhecido'}, extensão: {extension or 'sem extensão'}"
            )
        )
    
    # Criar diretório de uploads se não existir
    upload_dir = "uploads/audio/tracks"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Gerar nome de arquivo único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r"[^\w.\-]", "_", file.filename or "audio")
    filename = f"{timestamp}_{safe_name}"
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
        "mime_type": content_type or file.content_type,
        "file_size": os.path.getsize(file_path),
        "duration_seconds": duration_seconds,
        "category": category,
        "status": track_status,
        "notes": notes,
    }
    
    if current_user.role != "admin":
        track_data["tenant_id"] = str(current_user.tenant_id)
    
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
    new_status: AudioTrackStatusEnum = Query(..., alias="status")
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
    
    track = crud_audio_track.update_status(db, db_obj=track, status=new_status.value)
    return {"message": f"Status atualizado para {new_status.value}"}
