from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from core.dependencies import get_current_user
from core.models import Campaign, Device, PlaybackLog, User, ViewReport
from core.schemas_completos import (
    CampaignCreate, CampaignUpdate, CampaignResponse, CampaignStatusEnum
)
from crud.entidades import crud_campaign

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _invalidate_device_playlist_cache() -> None:
    from core.config import get_redis_client

    redis_client = get_redis_client()
    if not redis_client:
        return
    try:
        for key in redis_client.scan_iter("device_playlist:*"):
            redis_client.delete(key)
    except Exception as exc:
        print(f"[campaigns] Redis cache invalidation error: {exc}")


def _broadcast_playlist_invalidated(
    db: Session,
    campaign: Campaign,
    *,
    reason: str,
) -> None:
    """Pub/sub: notifica devices alvo de que a playlist foi alterada."""
    from services.event_bus import publish_campaign_event

    try:
        publish_campaign_event(
            db,
            campaign,
            event_type="playlist_invalidated",
            data={
                "config_version": campaign.config_version,
                "reason": reason,
            },
        )
    except Exception as exc:  # noqa: BLE001 — broadcast é best-effort
        print(f"[campaigns] broadcast playlist_invalidated failed: {exc}")


def _validate_campaign_device_ids(
    db: Session,
    *,
    device_ids: Optional[List[str]],
    tenant_id: Optional[str],
) -> None:
    if not device_ids:
        return

    normalized_ids = []
    for device_id in device_ids:
        if not device_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Lista de dispositivos contém ID vazio",
            )
        try:
            normalized_ids.append(str(UUID(str(device_id))))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"ID de dispositivo inválido: {device_id}",
            )

    devices = db.query(Device).filter(Device.id.in_(normalized_ids)).all()
    found_ids = {str(device.id) for device in devices}
    missing_ids = sorted(set(normalized_ids) - found_ids)
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Dispositivo(s) não encontrado(s): {', '.join(missing_ids)}",
        )

    if tenant_id:
        cross_tenant_ids = [
            str(device.id)
            for device in devices
            if str(device.tenant_id) != str(tenant_id)
        ]
        if cross_tenant_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Dispositivo(s) não pertencem ao tenant da campanha: "
                    f"{', '.join(cross_tenant_ids)}"
                ),
            )


def _sync_devices_for_campaign(db: Session, *, campaign: Campaign) -> None:
    selected_ids = {str(device_id) for device_id in (campaign.device_ids or [])}
    campaign_id = str(campaign.id)

    assigned_devices = db.query(Device).filter(Device.current_campaign_id == campaign.id).all()
    assigned_ids = {str(device.id) for device in assigned_devices}

    devices_by_id = {str(device.id): device for device in assigned_devices}
    if selected_ids:
        selected_devices = db.query(Device).filter(Device.id.in_(selected_ids)).all()
        devices_by_id.update({str(device.id): device for device in selected_devices})

    for device_id, device in devices_by_id.items():
        if device_id in selected_ids:
            device.current_campaign_id = campaign.id
            device.current_campaign = campaign.name
        elif device_id in assigned_ids:
            device.current_campaign_id = None
            device.current_campaign = None
        db.add(device)

    if selected_ids:
        other_campaigns = (
            db.query(Campaign)
            .filter(Campaign.id != campaign.id)
            .filter(Campaign.device_ids.isnot(None))
            .all()
        )
        for other_campaign in other_campaigns:
            original_ids = [str(device_id) for device_id in (other_campaign.device_ids or [])]
            filtered_ids = [device_id for device_id in original_ids if device_id not in selected_ids]
            if filtered_ids != original_ids:
                other_campaign.device_ids = filtered_ids
                db.add(other_campaign)

    db.commit()
    db.refresh(campaign)


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
    
    # Carregar playlist de áudio se existir
    from crud.entidades.crud_audio_playlist import crud_audio_playlist
    if campaign.audio_playlist_id:
        audio_playlist = crud_audio_playlist.get(db, id=str(campaign.audio_playlist_id))
        # Adicionar ao objeto campaign (não é um campo de modelo, apenas para resposta)
        campaign.audio_playlist = audio_playlist
    
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
        campaign_in.tenant_id = str(current_user.tenant_id)

    _validate_campaign_device_ids(
        db,
        device_ids=campaign_in.device_ids,
        tenant_id=campaign_in.tenant_id,
    )
    
    campaign = crud_campaign.create(db, obj_in=campaign_in)
    _sync_devices_for_campaign(db, campaign=campaign)
    _invalidate_device_playlist_cache()
    _broadcast_playlist_invalidated(db, campaign, reason="campaign_created")
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

    update_data = campaign_in.model_dump(exclude_unset=True)
    if "device_ids" in update_data:
        _validate_campaign_device_ids(
            db,
            device_ids=campaign_in.device_ids,
            tenant_id=str(campaign.tenant_id) if campaign.tenant_id else None,
        )
    
    campaign = crud_campaign.update(db, db_obj=campaign, obj_in=campaign_in)
    # Increment config_version to signal playlist change
    campaign = crud_campaign.increment_config_version(db, db_obj=campaign)
    if "device_ids" in update_data or "name" in update_data:
        _sync_devices_for_campaign(db, campaign=campaign)
    _invalidate_device_playlist_cache()
    _broadcast_playlist_invalidated(db, campaign, reason="campaign_updated")
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
    
    from services.event_bus import publish_device_event

    affected_device_ids = {
        str(row.id)
        for row in db.query(Device.id).filter(Device.current_campaign_id == campaign_id).all()
    }
    if campaign.device_ids:
        affected_device_ids.update(str(d) for d in campaign.device_ids if d)

    db.query(PlaybackLog).filter(PlaybackLog.campaign_id == campaign_id).delete(synchronize_session=False)
    db.query(ViewReport).filter(ViewReport.campaign_id == campaign_id).delete(synchronize_session=False)
    db.query(Device).filter(Device.current_campaign_id == campaign_id).update(
        {"current_campaign_id": None, "current_campaign": None},
        synchronize_session=False,
    )
    crud_campaign.remove(db, id=campaign_id)
    _invalidate_device_playlist_cache()
    for device_id in affected_device_ids:
        try:
            publish_device_event(
                device_id,
                event_type="playlist_invalidated",
                data={"reason": "campaign_deleted"},
                campaign_id=campaign_id,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[campaigns] broadcast delete failed for {device_id}: {exc}")
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
    # Increment config_version to signal playlist change
    campaign = crud_campaign.increment_config_version(db, db_obj=campaign)
    _invalidate_device_playlist_cache()
    _broadcast_playlist_invalidated(db, campaign, reason=f"status_changed:{status}")
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


# ─── Campaign actions ──────────────────────────────────────────────────────────

@router.post("/{campaign_id}/publish", response_model=CampaignResponse)
def publish_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = crud_campaign.get(db, id=campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    if current_user.role != "admin" and str(campaign.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")
    campaign = crud_campaign.update(db, db_obj=campaign, obj_in={"status": "active"})
    campaign = crud_campaign.increment_config_version(db, db_obj=campaign)
    _invalidate_device_playlist_cache()
    _broadcast_playlist_invalidated(db, campaign, reason="published")
    return campaign


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
def pause_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = crud_campaign.get(db, id=campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    if current_user.role != "admin" and str(campaign.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")
    campaign = crud_campaign.update(db, db_obj=campaign, obj_in={"status": "paused"})
    campaign = crud_campaign.increment_config_version(db, db_obj=campaign)
    _invalidate_device_playlist_cache()
    _broadcast_playlist_invalidated(db, campaign, reason="paused")
    return campaign


@router.post("/{campaign_id}/resume", response_model=CampaignResponse)
def resume_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = crud_campaign.get(db, id=campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    if current_user.role != "admin" and str(campaign.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")
    campaign = crud_campaign.update(db, db_obj=campaign, obj_in={"status": "active"})
    campaign = crud_campaign.increment_config_version(db, db_obj=campaign)
    _invalidate_device_playlist_cache()
    _broadcast_playlist_invalidated(db, campaign, reason="resumed")
    return campaign


@router.get("/{campaign_id}/stats")
def get_campaign_stats(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = crud_campaign.get(db, id=campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    if current_user.role != "admin" and str(campaign.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")

    playback_count = db.query(PlaybackLog).filter(
        PlaybackLog.campaign_id == campaign_id
    ).count()

    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "status": campaign.status.value if hasattr(campaign.status, "value") else campaign.status,
        "device_count": len(campaign.device_ids or []),
        "media_count": len(campaign.media_ids or []),
        "total_views": campaign.total_views or 0,
        "playback_count": playback_count,
    }
