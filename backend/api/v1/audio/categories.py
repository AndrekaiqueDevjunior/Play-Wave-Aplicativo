from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.dependencies import get_current_user
from core.models import User
from core.schemas_completos import (
    AudioCategoryCreate,
    AudioCategoryUpdate,
    AudioCategoryResponse,
)
from crud.entidades import crud_audio_category
from crud.entidades.crud_audio_category import default_categories, slugify

router = APIRouter(prefix="/audio/categories", tags=["audio-categories"])


def _resolve_tenant_id(current_user: User, tenant_id: Optional[str]) -> Optional[str]:
    """Admin pode informar tenant_id; demais usuários ficam presos ao próprio."""
    if current_user.role != "admin":
        return str(current_user.tenant_id)
    return tenant_id


@router.get("/", response_model=List[AudioCategoryResponse])
def list_audio_categories(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: Optional[str] = Query(None),
    include_defaults: bool = Query(True),
):
    """Lista categorias: padrão (virtuais) + personalizadas do tenant."""
    effective_tenant_id = _resolve_tenant_id(current_user, tenant_id)

    result: List[dict] = []
    if include_defaults:
        result.extend(default_categories())

    custom = crud_audio_category.get_by_tenant(db, tenant_id=effective_tenant_id)
    for cat in custom:
        result.append(
            {
                "id": str(cat.id),
                "tenant_id": str(cat.tenant_id) if cat.tenant_id else None,
                "name": cat.name,
                "slug": cat.slug,
                "is_default": cat.is_default,
                "created_at": cat.created_at,
                "updated_at": cat.updated_at,
            }
        )
    return result


@router.post("/", response_model=AudioCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_audio_category(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category_in: AudioCategoryCreate,
):
    """Cria categoria personalizada. Slug único por tenant; não colide com padrão."""
    effective_tenant_id = _resolve_tenant_id(current_user, category_in.tenant_id)

    slug = slugify(category_in.name)
    if not slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de categoria inválido",
        )
    if crud_audio_category.slug_is_taken(db, tenant_id=effective_tenant_id, slug=slug):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma categoria com esse nome",
        )

    category = crud_audio_category.create_for_tenant(
        db, name=category_in.name, tenant_id=effective_tenant_id
    )
    return AudioCategoryResponse(
        id=str(category.id),
        tenant_id=str(category.tenant_id) if category.tenant_id else None,
        name=category.name,
        slug=category.slug,
        is_default=category.is_default,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.put("/{category_id}", response_model=AudioCategoryResponse)
def update_audio_category(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category_id: str,
    category_in: AudioCategoryUpdate,
):
    """Renomeia categoria personalizada."""
    category = crud_audio_category.get(db, id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada",
        )
    if current_user.role != "admin" and str(category.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para alterar esta categoria",
        )

    slug = slugify(category_in.name)
    if not slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de categoria inválido",
        )
    if crud_audio_category.slug_is_taken(
        db, tenant_id=category.tenant_id, slug=slug, exclude_id=category_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma categoria com esse nome",
        )

    category = crud_audio_category.rename(db, db_obj=category, name=category_in.name)
    return AudioCategoryResponse(
        id=str(category.id),
        tenant_id=str(category.tenant_id) if category.tenant_id else None,
        name=category.name,
        slug=category.slug,
        is_default=category.is_default,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.delete("/{category_id}")
def delete_audio_category(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    category_id: str,
):
    """Remove categoria personalizada. Faixas vinculadas ficam sem category_id (FK SET NULL)."""
    category = crud_audio_category.get(db, id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoria não encontrada",
        )
    if current_user.role != "admin" and str(category.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para remover esta categoria",
        )

    crud_audio_category.remove(db, id=category_id)
    return {"message": "Categoria removida com sucesso"}
