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
from core.models import AudioPlaylistItem, AudioTrack, Campaign, Device, User
from core.schemas_completos import (
    AudioTrackCreate, AudioTrackUpdate, AudioTrackResponse,
    AudioTrackCategoryEnum, AudioTrackStatusEnum,
    AudioTrackUploadMultipleResponse, AudioTrackUploadError
)
from crud.entidades import crud_audio_track

router = APIRouter(prefix="/audio/tracks", tags=["audio-tracks"])

import logging
_log = logging.getLogger("playwave.audio_tracks")


def _device_ids_for_track(db: Session, track_id: str) -> set[str]:
    """Devices que reproduzem playlists contendo esta faixa."""
    playlist_ids = {
        str(row.playlist_id)
        for row in db.query(AudioPlaylistItem.playlist_id)
        .filter(AudioPlaylistItem.track_id == track_id)
        .all()
    }
    device_ids: set[str] = set()
    for pid in playlist_ids:
        rows = db.query(Device.id).filter(Device.audio_playlist_id == pid).all()
        device_ids.update(str(r.id) for r in rows)
        campaigns = db.query(Campaign).filter(Campaign.audio_playlist_id == pid).all()
        for c in campaigns:
            device_ids.update(str(d) for d in (c.device_ids or []) if d)
            rows2 = db.query(Device.id).filter(Device.current_campaign_id == c.id).all()
            device_ids.update(str(r.id) for r in rows2)
    return device_ids


def _notify_track_changed(db: Session, track_id: str, *, reason: str) -> None:
    """Invalida cache Redis e notifica players via SSE para todos os devices afetados."""
    device_ids = _device_ids_for_track(db, track_id)
    if not device_ids:
        return
    try:
        from core.config import get_redis_client
        redis = get_redis_client()
        if redis:
            pipe = redis.pipeline(transaction=False)
            for did in device_ids:
                pipe.delete(f"device_playlist:{did}")
            pipe.execute()
    except Exception as exc:
        _log.warning("track cache invalidation error: %s", exc)
    try:
        from services.event_bus import publish_device_event
        for did in device_ids:
            publish_device_event(did, event_type="playlist_invalidated", data={"reason": reason})
    except Exception as exc:
        _log.warning("track publish event error: %s", exc)


@router.get("/", response_model=List[AudioTrackResponse])
def get_audio_tracks(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    category: Optional[AudioTrackCategoryEnum] = Query(None),
    category_id: Optional[str] = Query(None),
    status: Optional[AudioTrackStatusEnum] = Query(None),
    tenant_id: Optional[str] = Query(None),
    # SPEC 016 — por padrão, faixas arquivadas não aparecem em nenhuma
    # listagem operacional (seletor de playlist/rádio, lista do admin).
    # include_archived=true é a forma explícita de ver arquivadas (ex.: para
    # restaurar). Quando `status` é passado explicitamente, respeita o filtro
    # pedido em vez de aplicar o default — permite continuar consultando
    # "status=archived" diretamente quando necessário.
    include_archived: bool = Query(False),
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
    if category_id:
        query = query.filter(AudioTrack.category_id == category_id)
    if status:
        query = query.filter(AudioTrack.status == status.value)
    elif not include_archived:
        query = query.filter(AudioTrack.status != "archived")
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

    return query.order_by(AudioTrack.created_at.desc()).offset(skip).limit(limit).all()


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
    category_id: Optional[str] = Form(None),
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
        "category_id": category_id or None,
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
    _notify_track_changed(db, track_id, reason="track.updated")
    return track


@router.delete("/{track_id}")
def delete_audio_track(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    track_id: str
):
    """
    Remove faixa de áudio definitivamente.

    SPEC 016 — bloqueia a exclusão com 409 e mensagem clara quando a faixa
    está em uso (playlist, pasta de rádio ou spot), em vez de deixar a
    constraint RESTRICT do banco estourar um IntegrityError genérico (500).
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

    refs = crud_audio_track.get_in_use_references(db, track_id=track_id)
    if refs["in_use"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Faixa em uso e não pode ser excluída definitivamente "
                f"(playlists: {refs['playlists']}, pastas: {refs['folders']}, "
                f"spots: {refs['spots']}). Arquive a faixa ou remova-a dos "
                "locais que a utilizam antes de excluir."
            ),
        )

    # Remover arquivo físico se existir
    if track.file_url and track.file_url.startswith("/uploads/"):
        file_path = track.file_url[1:]  # Remove o /
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass  # Ignora erro ao remover arquivo

    _notify_track_changed(db, track_id, reason="track.deleted")
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
    _notify_track_changed(db, track_id, reason="track.status_changed")
    return {"message": f"Status atualizado para {new_status.value}"}


@router.post("/upload-multiple", response_model=AudioTrackUploadMultipleResponse, status_code=status.HTTP_201_CREATED)
def upload_multiple_tracks(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    files: List[UploadFile] = File(...),
    category: Optional[AudioTrackCategoryEnum] = Form(None),
    category_id: Optional[str] = Form(None),
):
    """
    Upload múltiplo de faixas de áudio.

    Retorna lista com sucesso/falha para cada arquivo.
    """
    from services.ffprobe_service import get_audio_duration, FFprobeError

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum arquivo enviado",
        )

    if len(files) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Máximo 50 arquivos por vez",
        )

    os.makedirs("uploads/audio", exist_ok=True)
    uploaded_tracks = []
    errors = []

    for file in files:
        try:
            if not file.filename:
                errors.append({"filename": "unknown", "error": "Filename vazio"})
                continue

            # Validar tipo de arquivo
            if not file.content_type or not file.content_type.startswith("audio/"):
                errors.append({
                    "filename": file.filename,
                    "error": f"Tipo inválido: {file.content_type}. Apenas áudio.",
                })
                continue

            # Salvar arquivo temporário
            temp_path = f"uploads/audio/{datetime.utcnow().timestamp()}_{file.filename}"
            with open(temp_path, "wb") as buffer:
                buffer.write(file.file.read())

            # Extrair duração com ffprobe
            try:
                duration_seconds = get_audio_duration(temp_path)
                if not duration_seconds:
                    errors.append({
                        "filename": file.filename,
                        "error": "Não foi possível extrair duração",
                    })
                    os.remove(temp_path)
                    continue
            except FFprobeError as e:
                errors.append({
                    "filename": file.filename,
                    "error": str(e),
                })
                os.remove(temp_path)
                continue

            # Gerar nome final sanitizado
            safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', file.filename)
            file_url = f"/uploads/audio/{datetime.utcnow().isoformat()}_{safe_name}"

            # Mover para local final
            os.makedirs(os.path.dirname(file_url[1:]), exist_ok=True)
            shutil.move(temp_path, file_url[1:])

            # Criar registro
            track_name = file.filename.rsplit(".", 1)[0] if "." in file.filename else file.filename
            track = crud_audio_track.create(
                db,
                obj_in=AudioTrackCreate(
                    name=track_name,
                    file_url=file_url,
                    mime_type=file.content_type or "audio/mpeg",
                    duration_seconds=duration_seconds,
                    category=category or AudioTrackCategoryEnum.MUSIC,
                    category_id=category_id or None,
                    tenant_id=None if current_user.role == "admin" else str(current_user.tenant_id),
                ),
            )

            uploaded_tracks.append(track)

        except Exception as e:
            errors.append({
                "filename": file.filename or "unknown",
                "error": str(e),
            })
            # Tenta limpar arquivo temp se ainda existe
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass

    return AudioTrackUploadMultipleResponse(
        uploaded=uploaded_tracks,
        errors=errors if errors else None,
    )
