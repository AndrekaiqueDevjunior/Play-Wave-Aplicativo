from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from core.database import get_db
from core.dependencies import get_current_user
from core.models import Device, User
from core.schemas_completos import (
    LocationCreate, LocationUpdate, LocationResponse
)
from crud.entidades import crud_location

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/", response_model=List[LocationResponse])
def get_locations(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    tenant_id: Optional[str] = Query(None)
):
    """
    Lista localizações com filtros opcionais
    """
    # Se não for admin, filtra apenas do tenant do usuário
    if current_user.role != "admin" and not tenant_id:
        tenant_id = str(current_user.tenant_id)
    
    # Aplicar filtros específicos
    if tenant_id:
        locations = crud_location.get_by_tenant(db, tenant_id=tenant_id)
    elif search:
        locations = crud_location.search(db, query=search, skip=skip, limit=limit)
    else:
        locations = crud_location.get_multi(db, skip=skip, limit=limit)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        locations = [l for l in locations if str(l.tenant_id) == str(current_user.tenant_id)]
    
    return locations


@router.get("/{location_id}", response_model=LocationResponse)
def get_location(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    location_id: str
):
    """
    Obtém localização por ID
    """
    location = crud_location.get(db, id=location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Localização não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(location.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta localização"
        )
    
    return location


@router.get("/{location_id}/with-devices", response_model=LocationResponse)
def get_location_with_devices(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    location_id: str
):
    """
    Obtém localização com contagem de dispositivos
    """
    location = crud_location.get_with_devices(db, location_id=location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Localização não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(location.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta localização"
        )
    
    return location


@router.post("/", response_model=LocationResponse)
def create_location(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    location_in: LocationCreate
):
    """
    Cria nova localização
    """
    # Atribuir tenant se não for admin
    if current_user.role != "admin":
        location_in.tenant_id = current_user.tenant_id
    
    # Verificar se nome já existe no tenant
    existing_location = crud_location.get_by_name(db, name=location_in.name)
    if existing_location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de localização já existe"
        )
    
    location = crud_location.create(db, obj_in=location_in)
    return location


@router.put("/{location_id}", response_model=LocationResponse)
def update_location(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    location_id: str,
    location_in: LocationUpdate
):
    """
    Atualiza localização
    """
    location = crud_location.get(db, id=location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Localização não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(location.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta localização"
        )
    
    # Verificar se novo nome já existe (se estiver mudando)
    if location_in.name and location_in.name != location.name:
        existing_location = crud_location.get_by_name(db, name=location_in.name)
        if existing_location:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome de localização já existe"
            )
    
    location = crud_location.update(db, db_obj=location, obj_in=location_in)
    return location


@router.delete("/{location_id}")
def delete_location(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    location_id: str
):
    """
    Remove localização
    """
    location = crud_location.get(db, id=location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Localização não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(location.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para remover esta localização"
        )
    
    crud_location.remove(db, id=location_id)
    return {"message": "Localização removida com sucesso"}


@router.patch("/{location_id}/device-count")
def update_location_device_count(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    location_id: str
):
    """
    Atualiza contagem de dispositivos da localização
    """
    location = crud_location.get(db, id=location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Localização não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(location.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta localização"
        )
    
    location = crud_location.update_device_count(db, location_id=location_id)
    return {"message": "Contagem de dispositivos atualizada", "device_count": location.device_count}


@router.get("/statistics/overview")
def get_location_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém estatísticas das localizações
    """
    # Se não for admin, filtra apenas do tenant do usuário
    tenant_id = None if current_user.role == "admin" else str(current_user.tenant_id)
    
    total_locations = len(crud_location.get_by_tenant(db, tenant_id=tenant_id))
    
    # Calcular estatísticas adicionais
    locations = crud_location.get_by_tenant(db, tenant_id=tenant_id)
    total_devices = sum(loc.device_count or 0 for loc in locations)
    
    return {
        "total_locations": total_locations,
        "total_devices": total_devices,
        "avg_devices_per_location": total_devices / total_locations if total_locations > 0 else 0
    }


@router.get("/by-name/{name}", response_model=List[LocationResponse])
def get_locations_by_name(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    name: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Busca localizações por nome
    """
    locations = crud_location.search(db, query=name, skip=skip, limit=limit)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        locations = [l for l in locations if str(l.tenant_id) == str(current_user.tenant_id)]
    
    return locations


@router.get("/by-address/{address}", response_model=List[LocationResponse])
def get_locations_by_address(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    address: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Busca localizações por endereço
    """
    locations = crud_location.get_by_address(db, address=address)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        locations = [l for l in locations if str(l.tenant_id) == str(current_user.tenant_id)]
    
    return locations[skip:skip+limit]


@router.get("/{location_id}/devices")
def get_location_devices(
    location_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    location = crud_location.get(db, id=location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Localização não encontrada")
    if current_user.role != "admin" and str(location.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")

    devices = db.query(Device).filter(Device.location == location.name).all()
    return devices
