from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.dependencies import get_current_user
from core.models import User, UserRole
from core.schemas_completos import (
    UserCreate, UserUpdate, UserResponse, UserRoleEnum
)
from core.auth import get_password_hash
from crud.entidades import crud_user

router = APIRouter(prefix="/users", tags=["users"])


class StatusUpdate(BaseModel):
    is_active: bool


class RoleUpdate(BaseModel):
    role: UserRoleEnum


def _stamp_change(payload: dict, performed_by: User) -> dict:
    payload["last_changed_by"] = performed_by.email
    payload["last_changed_at"] = datetime.utcnow()
    return payload


@router.get("/", response_model=List[UserResponse])
def get_users(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    role: Optional[UserRoleEnum] = Query(None),
    tenant_id: Optional[str] = Query(None)
):
    """
    Lista usuários com filtros opcionais
    """
    # Apenas admin pode ver todos os usuários
    if current_user.role != "admin":
        if not tenant_id:
            tenant_id = str(current_user.tenant_id)
        elif str(tenant_id) != str(current_user.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para acessar usuários de outros tenants"
            )
    
    # Aplicar filtros específicos
    if role:
        users = crud_user.get_by_role(db, role=role)
    elif tenant_id:
        users = crud_user.get_by_tenant(db, tenant_id=tenant_id)
    elif search:
        users = crud_user.search(db, query=search, skip=skip, limit=limit)
    else:
        users = crud_user.get_multi(db, skip=skip, limit=limit)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        users = [u for u in users if str(u.tenant_id) == str(current_user.tenant_id)]
    
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: str
):
    """
    Obtém usuário por ID
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verificar permissão
    if (current_user.role != "admin" and 
        str(user.tenant_id) != str(current_user.tenant_id) and
        str(user.id) != str(current_user.id)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar este usuário"
        )
    
    return user


@router.post("/", response_model=UserResponse)
def create_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_in: UserCreate
):
    """
    Cria novo usuário
    """
    # Apenas admin ou operator pode criar usuários
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para criar usuários"
        )
    
    # Verificar se email já existe
    if crud_user.email_exists(db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Atribuir tenant se não for admin
    if current_user.role != "admin":
        user_in.tenant_id = current_user.tenant_id
        # Operator não pode criar admin
        if current_user.role == "operator" and user_in.role == UserRoleEnum.ADMIN:
            user_in.role = UserRoleEnum.OPERATOR

    user_data = user_in.model_dump(exclude_none=True)
    password = user_data.pop("password")
    user_data["password_hash"] = get_password_hash(password)
    user_data.setdefault("account_status", "active")
    user_data.setdefault("is_active", True)
    _stamp_change(user_data, current_user)

    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: str,
    user_in: UserUpdate
):
    """
    Atualiza usuário
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verificar permissão
    can_update = (
        current_user.role == "admin" or
        str(user.id) == str(current_user.id) or
        (str(user.tenant_id) == str(current_user.tenant_id) and current_user.role == "operator")
    )
    
    if not can_update:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar este usuário"
        )
    
    # Operator não pode promover para admin
    if (current_user.role == "operator" and 
        user_in.role == UserRoleEnum.ADMIN and
        str(user.id) != str(current_user.id)):
        user_in.role = UserRoleEnum.OPERATOR
    
    if user_in.account_status == "blocked":
        user_in.is_active = False
    elif user_in.account_status == "active":
        user_in.is_active = True

    # Verificar se novo email já existe
    if user_in.email and user_in.email != user.email:
        if crud_user.email_exists(db, email=user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado"
            )

    update_data = user_in.model_dump(exclude_unset=True)
    _stamp_change(update_data, current_user)
    user = crud_user.update(db, db_obj=user, obj_in=update_data)
    return user


@router.delete("/{user_id}")
def delete_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: str
):
    """
    Remove usuário
    """
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verificar permissão
    can_delete = (
        current_user.role == "admin" or
        (str(user.tenant_id) == str(current_user.tenant_id) and current_user.role == "operator")
    )
    
    if not can_delete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para remover este usuário"
        )
    
    # Não pode deletar a si mesmo
    if str(user.id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não pode remover seu próprio usuário"
        )
    
    crud_user.remove(db, id=user_id)
    return {"message": "Usuário removido com sucesso"}


@router.patch("/{user_id}/status")
def update_user_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: str,
    payload: StatusUpdate
):
    """
    Atualiza status do usuário (ativo/inativo)
    """
    is_active = payload.is_active
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verificar permissão
    can_update = (
        current_user.role == "admin" or
        (str(user.tenant_id) == str(current_user.tenant_id) and current_user.role == "operator")
    )
    
    if not can_update:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar este usuário"
        )
    
    # Não pode desativar a si mesmo
    if str(user.id) == str(current_user.id) and not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não pode desativar seu próprio usuário"
        )

    payload_data = {
        "is_active": is_active,
        "account_status": "active" if is_active else "inactive",
    }
    _stamp_change(payload_data, current_user)
    user = crud_user.update(db, db_obj=user, obj_in=payload_data)
    return {"message": f"Usuário {'ativado' if is_active else 'desativado'} com sucesso"}


@router.patch("/{user_id}/role")
def update_user_role(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: str,
    payload: RoleUpdate
):
    """
    Atualiza papel do usuário (apenas admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem alterar papéis"
        )

    role = payload.role
    user = crud_user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    # Não pode alterar próprio papel
    if str(user.id) == str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não pode alterar seu próprio papel"
        )

    payload_data = {"role": role}
    _stamp_change(payload_data, current_user)
    user = crud_user.update(db, db_obj=user, obj_in=payload_data)
    return {"message": f"Papel atualizado para {role.value} com sucesso"}


@router.get("/statistics/overview")
def get_user_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém estatísticas dos usuários
    """
    # Se não for admin, filtra apenas do tenant do usuário
    tenant_id = None if current_user.role == "admin" else str(current_user.tenant_id)
    
    total_users = len(crud_user.get_by_tenant(db, tenant_id=tenant_id))
    active_users = len([u for u in crud_user.get_by_tenant(db, tenant_id=tenant_id) if u.is_active])
    
    # Contagem por papel
    admin_count = len(crud_user.get_by_tenant_and_role(db, tenant_id=tenant_id, role="admin"))
    operator_count = len(crud_user.get_by_tenant_and_role(db, tenant_id=tenant_id, role="operator"))
    viewer_count = len(crud_user.get_by_tenant_and_role(db, tenant_id=tenant_id, role="viewer"))
    
    return {
        "total": total_users,
        "active": active_users,
        "inactive": total_users - active_users,
        "by_role": {
            "admin": admin_count,
            "operator": operator_count,
            "viewer": viewer_count
        }
    }


@router.get("/active/list", response_model=List[UserResponse])
def get_active_users(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista usuários ativos
    """
    users = crud_user.get_active(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        users = [u for u in users if str(u.tenant_id) == str(current_user.tenant_id)]
    
    return users[skip:skip+limit]


@router.get("/by-role/{role}", response_model=List[UserResponse])
def get_users_by_role(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    role: UserRoleEnum,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista usuários por papel
    """
    users = crud_user.get_by_role(db, role=role)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        users = [u for u in users if str(u.tenant_id) == str(current_user.tenant_id)]
    
    return users[skip:skip+limit]
