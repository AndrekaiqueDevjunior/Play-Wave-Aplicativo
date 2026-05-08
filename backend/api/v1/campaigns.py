from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from core.dependencies import get_current_user
from core.models import User
from core.schemas_completos import (
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignStatusEnum
)
from crud.entidades import crud_campaign

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.get("/", response_model=List[CampaignResponse])
def get_campaigns(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    status: Optional[CampaignStatusEnum] = Query(None),
    tenant_id: Optional[str] = Query(None)
):
    """
    Lista campanhas com filtros opcionais
    """
    # Se não for admin, filtra apenas do tenant do usuário
    if current_user.role != "admin" and not tenant_id:
        tenant_id = str(current_user.tenant_id)
    
    # Aplicar filtros específicos
    if status:
        campaigns = crud_campaign.get_by_status(db, status=status)
    elif tenant_id:
        campaigns = crud_campaign.get_by_tenant(db, tenant_id=tenant_id)
    elif search:
        campaigns = crud_campaign.search(db, query=search, skip=skip, limit=limit)
    else:
        campaigns = crud_campaign.get_multi(db, skip=skip, limit=limit)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        campaigns = [c for c in campaigns if str(c.tenant_id) == str(current_user.tenant_id)]
    
    return campaigns


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    campaign_id: str
):
    """
    Obtém campanha por ID
    """
    campaign = crud_campaign.get(db, id=campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(campaign.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta campanha"
        )
    
    return campaign


@router.post("/", response_model=CampaignResponse)
def create_campaign(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    campaign_in: CampaignCreate
):
    """
    Cria nova campanha
    """
    # Atribuir tenant se não for admin
    if current_user.role != "admin":
        campaign_in.tenant_id = current_user.tenant_id
    
    campaign = crud_campaign.create(db, obj_in=campaign_in)
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    campaign_id: str,
    campaign_in: CampaignUpdate
):
    """
    Atualiza campanha
    """
    campaign = crud_campaign.get(db, id=campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(campaign.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta campanha"
        )
    
    campaign = crud_campaign.update(db, db_obj=campaign, obj_in=campaign_in)
    return campaign


@router.delete("/{campaign_id}")
def delete_campaign(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    campaign_id: str
):
    """
    Remove campanha
    """
    campaign = crud_campaign.get(db, id=campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(campaign.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para remover esta campanha"
        )
    
    crud_campaign.remove(db, id=campaign_id)
    return {"message": "Campanha removida com sucesso"}


@router.patch("/{campaign_id}/status")
def update_campaign_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    campaign_id: str,
    status: CampaignStatusEnum
):
    """
    Atualiza status da campanha
    """
    campaign = crud_campaign.get(db, id=campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(campaign.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta campanha"
        )
    
    campaign = crud_campaign.update_status(db, db_obj=campaign, status=status)
    return {"message": f"Status atualizado para {status}"}


@router.post("/{campaign_id}/increment-views")
def increment_campaign_views(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    campaign_id: str
):
    """
    Incrementa contador de visualizações da campanha
    """
    campaign = crud_campaign.get(db, id=campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campanha não encontrada"
        )
    
    # Verificar permissão
    if current_user.role != "admin" and str(campaign.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para atualizar esta campanha"
        )
    
    campaign = crud_campaign.increment_views(db, campaign_id=campaign_id)
    return {"message": "Visualizações incrementadas", "total_views": campaign.total_views}


@router.get("/statistics/overview")
def get_campaign_statistics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtém estatísticas das campanhas
    """
    # Se não for admin, filtra apenas do tenant do usuário
    tenant_id = None if current_user.role == "admin" else str(current_user.tenant_id)
    
    statistics = crud_campaign.get_statistics(db, tenant_id=tenant_id)
    return statistics


@router.get("/active/list", response_model=List[CampaignResponse])
def get_active_campaigns(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista campanhas ativas
    """
    campaigns = crud_campaign.get_active(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        campaigns = [c for c in campaigns if str(c.tenant_id) == str(current_user.tenant_id)]
    
    return campaigns[skip:skip+limit]


@router.get("/scheduled/list", response_model=List[CampaignResponse])
def get_scheduled_campaigns(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista campanhas agendadas
    """
    campaigns = crud_campaign.get_scheduled(db)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        campaigns = [c for c in campaigns if str(c.tenant_id) == str(current_user.tenant_id)]
    
    return campaigns[skip:skip+limit]


@router.get("/by-priority/list", response_model=List[CampaignResponse])
def get_campaigns_by_priority(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    priority_min: int = Query(1, ge=1, le=10),
    priority_max: int = Query(10, ge=1, le=10),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista campanhas por faixa de prioridade
    """
    campaigns = crud_campaign.get_by_priority(db, priority_min=priority_min, priority_max=priority_max)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        campaigns = [c for c in campaigns if str(c.tenant_id) == str(current_user.tenant_id)]
    
    return campaigns[skip:skip+limit]


@router.get("/by-device/{device_id}", response_model=List[CampaignResponse])
def get_campaigns_by_device(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista campanhas associadas a um dispositivo
    """
    campaigns = crud_campaign.get_by_device(db, device_id=device_id)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        campaigns = [c for c in campaigns if str(c.tenant_id) == str(current_user.tenant_id)]
    
    return campaigns[skip:skip+limit]


@router.get("/by-media/{media_id}", response_model=List[CampaignResponse])
def get_campaigns_by_media(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    media_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Lista campanhas que usam uma mídia específica
    """
    campaigns = crud_campaign.get_by_media(db, media_id=media_id)
    
    # Filtrar por tenant se não for admin
    if current_user.role != "admin":
        campaigns = [c for c in campaigns if str(c.tenant_id) == str(current_user.tenant_id)]
    
    return campaigns[skip:skip+limit]
