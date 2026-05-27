from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from core.dependencies import get_current_user
from core.models import (
    Campaign,
    CampaignPlaylistItem,
    Device,
    Media,
    PlaybackLog,
    User,
    ViewReport,
)
from core.schemas_completos import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignStatusEnum,
    CampaignPlaylistItemCreate,
    CampaignPlaylistItemBulkCreate,
    CampaignPlaylistItemUpdate,
    CampaignPlaylistItemReorderPayload,
    CampaignPlaylistItemResponse,
)
from crud.entidades import crud_campaign
from crud.entidades.crud_campaign_playlist_item import crud_campaign_playlist_item

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


def _invalidate_device_playlist_cache(device_ids: Optional[set[str]] = None) -> None:
    from core.config import get_redis_client

    redis_client = get_redis_client()
    if not redis_client:
        return
    try:
        if device_ids is not None:
            if not device_ids:
                return
            pipe = redis_client.pipeline(transaction=False)
            for device_id in device_ids:
                pipe.delete(f"device_playlist:{device_id}")
            pipe.execute()
            return
        for key in redis_client.scan_iter("device_playlist:*"):
            redis_client.delete(key)
    except Exception as exc:
        print(f"[campaigns] Redis cache invalidation error: {exc}")


def _campaign_device_cache_keys(db: Session, campaign: Campaign) -> set[str]:
    device_ids = {str(device_id) for device_id in (campaign.device_ids or []) if device_id}
    if campaign.id:
        rows = db.query(Device.id).filter(Device.current_campaign_id == campaign.id).all()
        device_ids.update(str(row.id) for row in rows)
    return device_ids


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


def _normalize_uuid_list(
    values: Optional[List[str]],
    *,
    label: str,
) -> List[str]:
    if not values:
        return []

    normalized_ids = []
    seen_ids = set()
    for value in values:
        if not value:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Lista de {label} contém ID vazio",
            )
        try:
            normalized_id = str(UUID(str(value)))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"ID de {label} inválido: {value}",
            )
        if normalized_id not in seen_ids:
            normalized_ids.append(normalized_id)
            seen_ids.add(normalized_id)

    return normalized_ids


def _validate_campaign_device_ids(
    db: Session,
    *,
    device_ids: Optional[List[str]],
    tenant_id: Optional[str],
) -> List[str]:
    normalized_ids = _normalize_uuid_list(device_ids, label="dispositivos")
    if not normalized_ids:
        return []

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


    return normalized_ids


def _validate_campaign_media_refs(
    db: Session,
    *,
    media_ids: Optional[List[str]],
    media_order: Optional[List[dict]],
    tenant_id: Optional[str],
) -> tuple[List[str], Optional[List[dict]]]:
    normalized_media_ids = _normalize_uuid_list(media_ids, label="mídias")
    normalized_media_order = None

    if media_order is not None:
        normalized_media_order = []
        for item in media_order:
            item_data = item.model_dump() if hasattr(item, "model_dump") else dict(item)
            item_ids = _normalize_uuid_list([item_data.get("media_id")], label="mídias")
            item_data["media_id"] = item_ids[0]
            normalized_media_order.append(item_data)

    referenced_ids = set(normalized_media_ids)
    if normalized_media_order:
        referenced_ids.update(item["media_id"] for item in normalized_media_order)

    if not referenced_ids:
        return normalized_media_ids, normalized_media_order

    media_items = db.query(Media).filter(Media.id.in_(referenced_ids)).all()
    found_ids = {str(media.id) for media in media_items}
    missing_ids = sorted(referenced_ids - found_ids)
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Mídia(s) não encontrada(s): {', '.join(missing_ids)}",
        )

    if tenant_id:
        cross_tenant_ids = [
            str(media.id)
            for media in media_items
            if str(media.tenant_id) != str(tenant_id)
        ]
        if cross_tenant_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Mídia(s) não pertencem ao tenant da campanha: "
                    f"{', '.join(cross_tenant_ids)}"
                ),
            )

    return normalized_media_ids, normalized_media_order


def _validate_campaign_relationships(
    db: Session,
    *,
    campaign_in: CampaignCreate | CampaignUpdate,
    tenant_id: Optional[str],
) -> None:
    payload = campaign_in.model_dump(exclude_unset=True)
    if "device_ids" in payload:
        campaign_in.device_ids = _validate_campaign_device_ids(
            db,
            device_ids=campaign_in.device_ids,
            tenant_id=tenant_id,
        )

    if "media_ids" in payload or "media_order" in payload:
        normalized_media_ids, normalized_media_order = _validate_campaign_media_refs(
            db,
            media_ids=campaign_in.media_ids,
            media_order=campaign_in.media_order,
            tenant_id=tenant_id,
        )
        if "media_ids" in payload:
            campaign_in.media_ids = normalized_media_ids
        if "media_order" in payload:
            campaign_in.media_order = normalized_media_order


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

    _validate_campaign_relationships(
        db,
        campaign_in=campaign_in,
        tenant_id=campaign_in.tenant_id,
    )
    
    campaign = crud_campaign.create(db, obj_in=campaign_in)
    _sync_devices_for_campaign(db, campaign=campaign)
    _invalidate_device_playlist_cache(_campaign_device_cache_keys(db, campaign))
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
    affected_device_ids = _campaign_device_cache_keys(db, campaign)
    _validate_campaign_relationships(
        db,
        campaign_in=campaign_in,
        tenant_id=str(campaign.tenant_id) if campaign.tenant_id else None,
    )
    
    campaign = crud_campaign.update(db, db_obj=campaign, obj_in=campaign_in)
    # Increment config_version to signal playlist change
    campaign = crud_campaign.increment_config_version(db, db_obj=campaign)
    if "device_ids" in update_data or "name" in update_data:
        _sync_devices_for_campaign(db, campaign=campaign)
    affected_device_ids.update(_campaign_device_cache_keys(db, campaign))
    _invalidate_device_playlist_cache(affected_device_ids)
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
    _invalidate_device_playlist_cache(affected_device_ids)
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
    new_status: CampaignStatusEnum = Query(..., alias="status")
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

    campaign = crud_campaign.update_status(db, db_obj=campaign, status=new_status)
    # Increment config_version to signal playlist change
    campaign = crud_campaign.increment_config_version(db, db_obj=campaign)
    _invalidate_device_playlist_cache(_campaign_device_cache_keys(db, campaign))
    _broadcast_playlist_invalidated(db, campaign, reason=f"status_changed:{new_status}")
    return {"message": f"Status atualizado para {new_status}"}


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
    _invalidate_device_playlist_cache(_campaign_device_cache_keys(db, campaign))
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
    _invalidate_device_playlist_cache(_campaign_device_cache_keys(db, campaign))
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
    _invalidate_device_playlist_cache(_campaign_device_cache_keys(db, campaign))
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


# ---------------------------------------------------------------------------
# SPEC-002: Campaign Playlist Items
# ---------------------------------------------------------------------------

def _authorize_campaign_access(
    db: Session,
    *,
    campaign_id: str,
    current_user: User,
) -> Campaign:
    campaign = crud_campaign.get(db, id=campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    if current_user.role != "admin" and str(campaign.tenant_id) != str(current_user.tenant_id):
        raise HTTPException(status_code=403, detail="Sem permissão")
    return campaign


def _ensure_media_in_tenant(
    db: Session,
    *,
    media_id: str,
    tenant_id: Optional[str],
) -> Media:
    try:
        normalized_id = str(UUID(str(media_id)))
    except ValueError:
        raise HTTPException(status_code=422, detail=f"ID de mídia inválido: {media_id}")
    media = db.query(Media).filter(Media.id == normalized_id).first()
    if not media:
        raise HTTPException(status_code=422, detail=f"Mídia não encontrada: {media_id}")
    if tenant_id and str(media.tenant_id) != str(tenant_id):
        raise HTTPException(status_code=422, detail="Mídia não pertence ao tenant da campanha")
    return media


def _sync_legacy_media_fields(db: Session, *, campaign: Campaign) -> None:
    """Mirror playlist items back into the legacy media_ids/media_order JSON columns.

    Kept as a transition shim while the player builder and frontend migrate to
    the relational items. Drop this once both consumers are converted.
    """
    items = crud_campaign_playlist_item.list_by_campaign(
        db, campaign_id=str(campaign.id)
    )
    legacy_ids: List[str] = []
    legacy_order: List[dict] = []
    seen_ids: set[str] = set()
    for item in items:
        if not item.is_active:
            continue
        media_id_str = str(item.media_id)
        if media_id_str not in seen_ids:
            legacy_ids.append(media_id_str)
            seen_ids.add(media_id_str)
        legacy_order.append(
            {
                "media_id": media_id_str,
                "duration": item.display_duration_seconds or 0,
            }
        )
    campaign.media_ids = legacy_ids
    campaign.media_order = legacy_order
    db.add(campaign)


def _bump_and_invalidate(db: Session, *, campaign: Campaign, reason: str) -> Campaign:
    campaign = crud_campaign.increment_config_version(db, db_obj=campaign)
    _invalidate_device_playlist_cache(_campaign_device_cache_keys(db, campaign))
    _broadcast_playlist_invalidated(db, campaign, reason=reason)
    return campaign


@router.get(
    "/{campaign_id}/items",
    response_model=List[CampaignPlaylistItemResponse],
)
def list_campaign_items(
    *,
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = _authorize_campaign_access(
        db, campaign_id=campaign_id, current_user=current_user
    )
    return crud_campaign_playlist_item.list_by_campaign(
        db, campaign_id=str(campaign.id)
    )


@router.post(
    "/{campaign_id}/items",
    response_model=List[CampaignPlaylistItemResponse],
    status_code=status.HTTP_201_CREATED,
)
def add_campaign_items(
    *,
    campaign_id: str,
    payload: CampaignPlaylistItemBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = _authorize_campaign_access(
        db, campaign_id=campaign_id, current_user=current_user
    )

    next_index = crud_campaign_playlist_item.next_order_index(
        db, campaign_id=str(campaign.id)
    )

    created: List[CampaignPlaylistItem] = []
    for entry in payload.items:
        _ensure_media_in_tenant(
            db,
            media_id=entry.media_id,
            tenant_id=str(campaign.tenant_id) if campaign.tenant_id else None,
        )
        order_index = entry.order_index if entry.order_index is not None else next_index
        if entry.order_index is None:
            next_index += 10
        item = CampaignPlaylistItem(
            campaign_id=campaign.id,
            media_id=entry.media_id,
            order_index=order_index,
            display_duration_seconds=entry.display_duration_seconds,
            starts_at=entry.starts_at,
            ends_at=entry.ends_at,
            is_active=entry.is_active if entry.is_active is not None else True,
            repeat_count=entry.repeat_count or 1,
        )
        db.add(item)
        created.append(item)

    db.flush()
    crud_campaign_playlist_item.compact_order(db, campaign_id=str(campaign.id))
    _sync_legacy_media_fields(db, campaign=campaign)
    db.commit()
    _bump_and_invalidate(db, campaign=campaign, reason="playlist_items_added")
    for item in created:
        db.refresh(item)
    return crud_campaign_playlist_item.list_by_campaign(
        db, campaign_id=str(campaign.id)
    )


@router.put(
    "/{campaign_id}/items/{item_id}",
    response_model=CampaignPlaylistItemResponse,
)
def update_campaign_item(
    *,
    campaign_id: str,
    item_id: str,
    payload: CampaignPlaylistItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = _authorize_campaign_access(
        db, campaign_id=campaign_id, current_user=current_user
    )
    item = crud_campaign_playlist_item.get(db, item_id=item_id)
    if not item or str(item.campaign_id) != str(campaign.id):
        raise HTTPException(status_code=404, detail="Item de playlist não encontrado")

    data = payload.model_dump(exclude_unset=True)
    if "media_id" in data and data["media_id"]:
        _ensure_media_in_tenant(
            db,
            media_id=data["media_id"],
            tenant_id=str(campaign.tenant_id) if campaign.tenant_id else None,
        )

    for field, value in data.items():
        setattr(item, field, value)
    db.add(item)
    db.flush()

    if "order_index" in data:
        crud_campaign_playlist_item.compact_order(db, campaign_id=str(campaign.id))

    _sync_legacy_media_fields(db, campaign=campaign)
    db.commit()
    _bump_and_invalidate(db, campaign=campaign, reason="playlist_item_updated")
    db.refresh(item)
    return item


@router.delete("/{campaign_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_campaign_item(
    *,
    campaign_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = _authorize_campaign_access(
        db, campaign_id=campaign_id, current_user=current_user
    )
    item = crud_campaign_playlist_item.get(db, item_id=item_id)
    if not item or str(item.campaign_id) != str(campaign.id):
        raise HTTPException(status_code=404, detail="Item de playlist não encontrado")

    db.delete(item)
    db.flush()
    crud_campaign_playlist_item.compact_order(db, campaign_id=str(campaign.id))
    _sync_legacy_media_fields(db, campaign=campaign)
    db.commit()
    _bump_and_invalidate(db, campaign=campaign, reason="playlist_item_removed")
    return None


@router.patch(
    "/{campaign_id}/items/reorder",
    response_model=List[CampaignPlaylistItemResponse],
)
def reorder_campaign_items(
    *,
    campaign_id: str,
    payload: CampaignPlaylistItemReorderPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    campaign = _authorize_campaign_access(
        db, campaign_id=campaign_id, current_user=current_user
    )
    entries = [
        {"item_id": entry.item_id, "order_index": entry.order_index}
        for entry in payload.items
    ]
    items = crud_campaign_playlist_item.apply_reorder(
        db, campaign_id=str(campaign.id), entries=entries
    )
    _sync_legacy_media_fields(db, campaign=campaign)
    db.commit()
    _bump_and_invalidate(db, campaign=campaign, reason="playlist_reordered")
    return items
