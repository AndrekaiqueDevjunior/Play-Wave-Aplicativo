from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
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
    MediaCreate, MediaUpdate, MediaResponse, MediaTypeEnum, MediaStatusEnum
)
from crud.entidades import crud_media
from core.config import settings

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/", response_model=List[MediaResponse])
def get_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    media_type: Optional[MediaTypeEnum] = Query(None),
    status: Optional[MediaStatusEnum] = Query(None),
    category: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None)
):
    """
    Lista mídias com filtros opcionais
    """
    # Se não for admin, filtra apenas do tenant do usuário
    if current_user.role != "admin" and not tenant_id:
        tenant_id = str(current_user.tenant_id)
    
    # Aplicar filtros específicos
    if media_type:
        media_list = crud_media.get_by_type(db, media_type=media_type)
    elif status:
        media_list = crud_media.get_by_status(db, status=status)
    elif category:
        media_list = crud_media.get_by_category(db, category=category)
    elif tags:
        tag_list = tags.split(",") if tags else []
        media_list = crud_media.get_by_tags(db, tags=tag_list)
    elif tenant_id:
        media_list = crud_media.get_by_tenant(db, tenant_id=tenant_id)
    elif search:
        media_list = crud_media.search(db, query=search, skip=skip, limit=limit)
    else:
        media_list = crud_media.get_multi(db, skip=skip, limit=limit)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        media_list = [m for m in media_list if str(m.tenant_id) == str(current_user.tenant_id)]
    
    return media_list


@router.get("/{media_id}", response_model=MediaResponse)
def get_media_by_id(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_id: str
):
    """
    Obtém mídia por ID
    """
    media = crud_media.get(db, id=media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mídia não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(media.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta mídia"
        )
    
    return media


@router.post("/", response_model=MediaResponse)
def create_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_in: MediaCreate
):
    """
    Cria nova mídia (metadados)
    """
    # Atribuir tenant se não for admin
    if current_user.role != "admin":
        media_in.tenant_id = current_user.tenant_id
    
    media = crud_media.create(db, obj_in=media_in)
    return media


@router.post("/upload", response_model=MediaResponse)
def upload_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    file: UploadFile = File(...),
    name: str = Form(...),
    media_type: MediaTypeEnum = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    duration: Optional[int] = Form(None),
    notes: Optional[str] = Form(None)
):
    """
    Faz upload de arquivo de mídia
    """
    # Validar tipo de arquivo
    allowed_types = {
        "image": ["image/jpeg", "image/png", "image/gif", "image/webp"],
        "video": ["video/mp4", "video/avi", "video/mov", "video/webm"],
        "audio": ["audio/mp3", "audio/wav", "audio/ogg", "audio/m4a"]
    }
    
    if file.content_type not in allowed_types.get(media_type, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de arquivo não permitido para {media_type}"
        )
    
    # Criar diretório de uploads se não existir
    upload_dir = "uploads/media"
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
    
    # Criar mídia no banco
    media_data = {
        "name": name,
        "description": description,
        "file_url": f"/uploads/media/{filename}",
        "type": media_type,
        "mime_type": file.content_type,
        "file_size": os.path.getsize(file_path),
        "duration": duration,
        "tags": tags.split(",") if tags else [],
        "category": category,
        "notes": notes,
    }
    
    if current_user.role != "admin":
        media_data["tenant_id"] = current_user.tenant_id
    
    media = crud_media.create(db, obj_in=MediaCreate(**media_data))
    return media


@router.put("/{media_id}", response_model=MediaResponse)
def update_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_id: str,
    media_in: MediaUpdate
):
    """
    Atualiza mídia
    """
    media = crud_media.get(db, id=media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mídia não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(media.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta mídia"
        )
    
    media = crud_media.update(db, db_obj=media, obj_in=media_in)
    return media


@router.delete("/{media_id}")
def delete_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_id: str
):
    """
    Remove mídia
    """
    media = crud_media.get(db, id=media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mídia não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(media.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para remover esta mídia"
        )
    
    # Remover arquivo físico se existir
    if media.file_url and media.file_url.startswith("/uploads/"):
        file_path = media.file_url[1:]  # Remove o /
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass  # Ignora erro ao remover arquivo
    
    crud_media.remove(db, id=media_id)
    return {"message": "Mídia removida com sucesso"}


@router.patch("/{media_id}/status")
def update_media_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_id: str,
    status: MediaStatusEnum
):
    """
    Atualiza status da mídia
    """
    media = crud_media.get(db, id=media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mídia não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(media.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta mídia"
        )
    
    media = crud_media.update_status(db, db_obj=media, status=status)
    return {"message": f"Status atualizado para {status}"}


@router.get("/statistics/overview")
def get_media_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém estatísticas das mídias
    """
    # Se não for admin, filtra apenas do tenant do usuário
    tenant_id = None if current_user.role == "admin" else str(current_user.tenant_id)
    
    statistics = crud_media.get_statistics(db, tenant_id=tenant_id)
    return statistics


@router.get("/available/list", response_model=List[MediaResponse])
def get_available_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista mídias disponíveis para uso
    """
    media_list = crud_media.get_available(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        media_list = [m for m in media_list if str(m.tenant_id) == str(current_user.tenant_id)]
    
    return media_list[skip:skip+limit]


@router.get("/processing/list", response_model=List[MediaResponse])
def get_processing_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista mídias em processamento
    """
    media_list = crud_media.get_processing(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        media_list = [m for m in media_list if str(m.tenant_id) == str(current_user.tenant_id)]
    
    return media_list[skip:skip+limit]


@router.get("/error/list", response_model=List[MediaResponse])
def get_error_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista mídias com erro
    """
    media_list = crud_media.get_with_error(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        media_list = [m for m in media_list if str(m.tenant_id) == str(current_user.tenant_id)]
    
    return media_list[skip:skip+limit]


@router.get("/by-type/{media_type}", response_model=List[MediaResponse])
def get_media_by_type(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_type: MediaTypeEnum,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista mídias por tipo
    """
    media_list = crud_media.get_by_type(db, media_type=media_type)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        media_list = [m for m in media_list if str(m.tenant_id) == str(current_user.tenant_id)]
    
    return media_list[skip:skip+limit]


@router.get("/by-category/{category}", response_model=List[MediaResponse])
def get_media_by_category(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista mídias por categoria
    """
    media_list = crud_media.get_by_category(db, category=category)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        media_list = [m for m in media_list if str(m.tenant_id) == str(current_user.tenant_id)]
    
    return media_list[skip:skip+limit]
