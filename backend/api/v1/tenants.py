from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user, require_role
from core.models import User
from core.schemas_completos import TenantCreate, TenantUpdate, TenantResponse
from crud.entidades import crud_tenant

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/me", response_model=TenantResponse)
def get_my_tenant(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Usuário sem tenant associado")
    tenant = crud_tenant.get(db, id=str(current_user.tenant_id))
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return tenant


@router.put("/me", response_model=TenantResponse)
def update_my_tenant(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
    tenant_in: TenantUpdate,
):
    if not current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Usuário sem tenant associado")
    tenant = crud_tenant.get(db, id=str(current_user.tenant_id))
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return crud_tenant.update(db, db_obj=tenant, obj_in=tenant_in)


# ─── Superadmin routes ────────────────────────────────────────────────────────

@router.get("/", response_model=List[TenantResponse])
def list_tenants(
    *,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    skip: int = 0,
    limit: int = 100,
):
    return crud_tenant.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    *,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_in: TenantCreate,
):
    return crud_tenant.create(db, obj_in=tenant_in)


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(
    tenant_id: str,
    *,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    tenant = crud_tenant.get(db, id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: str,
    *,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    tenant_in: TenantUpdate,
):
    tenant = crud_tenant.get(db, id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    return crud_tenant.update(db, db_obj=tenant, obj_in=tenant_in)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant_id: str,
    *,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    tenant = crud_tenant.get(db, id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    crud_tenant.remove(db, id=tenant_id)
