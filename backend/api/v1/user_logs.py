from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.dependencies import get_current_user
from core.models import User
from core.schemas_completos import (
    UserLogCreate, UserLogResponse, UserLogActionEnum
)
from crud.entidades import crud_user_log

router = APIRouter(prefix="/user-logs", tags=["user-logs"])


@router.get("/", response_model=List[UserLogResponse])
def get_user_logs(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    action: Optional[UserLogActionEnum] = Query(None),
    target_user_id: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None)
):
    """
    Lista logs de usuários com filtros opcionais
    """
    if current_user.role != "admin" and not tenant_id:
        tenant_id = str(current_user.tenant_id)

    if action:
        logs = crud_user_log.get_by_action(db, action=action)
    elif target_user_id:
        logs = crud_user_log.get_by_target_user(db, target_user_id=target_user_id)
    elif tenant_id:
        logs = crud_user_log.get_by_tenant(db, tenant_id=tenant_id)
    elif search:
        logs = crud_user_log.search(db, query=search, skip=skip, limit=limit)
    else:
        logs = crud_user_log.get_multi(db, skip=skip, limit=limit)

    if current_user.role != "admin":
        logs = [l for l in logs if str(l.tenant_id) == str(current_user.tenant_id)]

    return logs


@router.post("/", response_model=UserLogResponse)
def create_user_log(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    log_in: UserLogCreate
):
    """
    Cria novo log de usuário
    """
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para criar logs"
        )

    tenant_id = log_in.tenant_id
    if current_user.role != "admin":
        tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    elif tenant_id is None and current_user.tenant_id:
        tenant_id = str(current_user.tenant_id)

    log = crud_user_log.create_log(
        db,
        target_user_id=log_in.target_user_id,
        action=log_in.action,
        performed_by=current_user.email,
        target_user_email=log_in.target_user_email,
        details=log_in.details,
        tenant_id=tenant_id,
    )

    return log


@router.get("/statistics/overview")
def get_user_log_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(7, ge=1, le=365)
):
    """
    Obtém estatísticas dos logs de usuários
    """
    tenant_id = None if current_user.role == "admin" else str(current_user.tenant_id)
    statistics = crud_user_log.get_statistics(db, tenant_id=tenant_id, days=days)
    return statistics


@router.get("/recent", response_model=List[UserLogResponse])
def get_recent_logs(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=500)
):
    """
    Lista logs mais recentes
    """
    logs = crud_user_log.get_multi(db, skip=0, limit=limit)
    if current_user.role != "admin":
        logs = [l for l in logs if str(l.tenant_id) == str(current_user.tenant_id)]
    return logs


@router.get("/by-user/{user_id}", response_model=List[UserLogResponse])
def get_logs_by_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista logs de um usuário específico
    """
    if current_user.role != "admin" and str(user_id) != str(current_user.id):
        # Operadores podem ver logs de usuários do mesmo tenant
        if current_user.role != "operator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para acessar logs de outros usuários"
            )

    logs = crud_user_log.get_by_target_user(db, target_user_id=user_id)

    if current_user.role != "admin":
        logs = [l for l in logs if str(l.tenant_id) == str(current_user.tenant_id)]

    return logs[skip:skip + limit]


@router.get("/by-action/{action}", response_model=List[UserLogResponse])
def get_logs_by_action(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    action: UserLogActionEnum,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista logs por tipo de ação
    """
    logs = crud_user_log.get_by_action(db, action=action)
    if current_user.role != "admin":
        logs = [l for l in logs if str(l.tenant_id) == str(current_user.tenant_id)]
    return logs[skip:skip + limit]


@router.get("/{log_id}", response_model=UserLogResponse)
def get_user_log(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    log_id: str
):
    """
    Obtém log de usuário por ID
    """
    log = crud_user_log.get(db, id=log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log não encontrado"
        )

    if current_user.role != "admin" and str(log.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar este log"
        )

    return log
