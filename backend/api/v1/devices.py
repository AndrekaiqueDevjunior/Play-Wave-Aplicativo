from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from core.dependencies import get_current_user
from core.models import User
from core.schemas_completos import (
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceStatusEnum
)
from crud.entidades import crud_device

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/", response_model=List[DeviceResponse])
def get_devices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    status: Optional[DeviceStatusEnum] = Query(None),
    device_type: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    group: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None)
):
    """
    Lista dispositivos com filtros opcionais
    """
    # Se não for admin, filtra apenas do tenant do usuário
    if current_user.role != "admin" and not tenant_id:
        tenant_id = str(current_user.tenant_id)
    
    # Aplicar filtros específicos
    if status:
        devices = crud_device.get_by_status(db, status=status)
    elif device_type:
        devices = crud_device.get_by_type(db, device_type=device_type)
    elif location:
        devices = crud_device.get_by_location(db, location=location)
    elif group:
        devices = crud_device.get_by_group(db, group=group)
    elif tenant_id:
        devices = crud_device.get_by_tenant(db, tenant_id=tenant_id)
    elif search:
        devices = crud_device.search(db, query=search, skip=skip, limit=limit)
    else:
        devices = crud_device.get_multi(db, skip=skip, limit=limit)
    
    return devices


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str
):
    """
    Obtém dispositivo por ID
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar este dispositivo"
        )
    
    return device


@router.post("/", response_model=DeviceResponse)
def create_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_in: DeviceCreate
):
    """
    Cria novo dispositivo
    """
    # Verificar se código de pareamento já existe
    existing_device = crud_device.get_by_pairing_code(db, pairing_code=device_in.pairing_code)
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de pareamento já existe"
        )
    
    # Atribuir tenant se não for admin
    if current_user.role != "admin":
        device_in.tenant_id = current_user.tenant_id
    
    device = crud_device.create(db, obj_in=device_in)
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
    device_in: DeviceUpdate
):
    """
    Atualiza dispositivo
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar este dispositivo"
        )
    
    # Verificar se novo código de pareamento já existe
    if device_in.pairing_code and device_in.pairing_code != device.pairing_code:
        existing_device = crud_device.get_by_pairing_code(db, pairing_code=device_in.pairing_code)
        if existing_device:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de pareamento já existe"
            )
    
    device = crud_device.update(db, db_obj=device, obj_in=device_in)
    return device


@router.delete("/{device_id}")
def delete_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str
):
    """
    Remove dispositivo
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para remover este dispositivo"
        )
    
    crud_device.remove(db, id=device_id)
    return {"message": "Dispositivo removido com sucesso"}


@router.patch("/{device_id}/status")
def update_device_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
    status: DeviceStatusEnum
):
    """
    Atualiza status do dispositivo
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar este dispositivo"
        )
    
    device = crud_device.update_status(db, db_obj=device, status=status)
    return {"message": f"Status atualizado para {status}"}


@router.post("/{device_id}/block")
def block_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str
):
    """
    Bloqueia dispositivo
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para bloquear este dispositivo"
        )
    
    device = crud_device.block_device(db, db_obj=device)
    return {"message": "Dispositivo bloqueado com sucesso"}


@router.post("/{device_id}/unblock")
def unblock_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str
):
    """
    Desbloqueia dispositivo
    """
    device = crud_device.get(db, id=device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispositivo não encontrado"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(device.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para desbloquear este dispositivo"
        )
    
    device = crud_device.unblock_device(db, db_obj=device)
    return {"message": "Dispositivo desbloqueado com sucesso"}


@router.get("/statistics/overview")
def get_device_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém estatísticas dos dispositivos
    """
    # Se não for admin, filtra apenas do tenant do usuário
    tenant_id = None if current_user.role == "admin" else str(current_user.tenant_id)
    
    statistics = crud_device.get_statistics(db, tenant_id=tenant_id)
    return statistics


@router.get("/online/list", response_model=List[DeviceResponse])
def get_online_devices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista dispositivos online
    """
    devices = crud_device.get_online(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        devices = [d for d in devices if str(d.tenant_id) == str(current_user.tenant_id)]
    
    return devices[skip:skip+limit]


@router.get("/offline/list", response_model=List[DeviceResponse])
def get_offline_devices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista dispositivos offline
    """
    devices = crud_device.get_offline(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        devices = [d for d in devices if str(d.tenant_id) == str(current_user.tenant_id)]
    
    return devices[skip:skip+limit]


@router.get("/pairing/waiting", response_model=List[DeviceResponse])
def get_waiting_pairing_devices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista dispositivos aguardando pareamento
    """
    devices = crud_device.get_waiting_pairing(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        devices = [d for d in devices if str(d.tenant_id) == str(current_user.tenant_id)]
    
    return devices[skip:skip+limit]
