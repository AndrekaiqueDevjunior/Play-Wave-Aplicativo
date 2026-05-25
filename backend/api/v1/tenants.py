import uuid
from typing import Dict, List, Set

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user, require_role
from core.models import Campaign, Device, User
from core.schemas_completos import (
    TenantAudioConfigUpdate,
    TenantCreate,
    TenantOSDConfigUpdate,
    TenantResponse,
    TenantUpdate,
)
from crud.entidades import crud_tenant

router = APIRouter(prefix="/tenants", tags=["tenants"])

OSD_TENANT_FIELDS = {
    "show_current_audio": "osd_show_current_audio",
    "position": "osd_position",
    "duration_seconds": "osd_duration_seconds",
    "opacity": "osd_opacity",
    "font_size": "osd_font_size",
}

OSD_DEVICE_FIELDS = {
    "show_current_audio": "osd_show_current_audio",
    "position": "osd_position",
    "duration_seconds": "osd_duration_seconds",
    "opacity": "osd_opacity",
    "font_size": "osd_font_size",
}


def _enum_value(value):
    return value.value if hasattr(value, "value") else value


def _invalidate_device_playlist_cache(device_ids: Set[str]) -> None:
    from core.config import get_redis_client

    if not device_ids:
        return
    redis_client = get_redis_client()
    if not redis_client:
        return
    try:
        pipe = redis_client.pipeline(transaction=False)
        for device_id in device_ids:
            pipe.delete(f"device_playlist:{device_id}")
        pipe.execute()
    except Exception as exc:
        print(f"[tenants] Redis cache invalidation error: {exc}")


def _broadcast_playlist_invalidated(devices_by_campaign: Dict[str, str | None], *, reason: str) -> None:
    from services.event_bus import publish_device_event

    for device_id, campaign_id in devices_by_campaign.items():
        try:
            publish_device_event(
                device_id,
                event_type="playlist_invalidated",
                campaign_id=campaign_id,
                data={"reason": reason},
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[tenants] broadcast playlist_invalidated failed for {device_id}: {exc}")


def _devices_by_campaign_for_tenant(db: Session, *, tenant_id: str) -> Dict[str, str | None]:
    devices_by_campaign: Dict[str, str | None] = {}
    rows = (
        db.query(Device.id, Device.current_campaign_id)
        .filter(Device.tenant_id == tenant_id)
        .all()
    )
    for row in rows:
        devices_by_campaign[str(row.id)] = (
            str(row.current_campaign_id) if row.current_campaign_id else None
        )
    return devices_by_campaign


def _touch_tenant_audio_campaigns(
    db: Session,
    *,
    tenant_id: str,
    policy_changed: bool,
    fade_changed: bool,
) -> None:
    if not policy_changed and not fade_changed:
        return

    query = db.query(Campaign).filter(Campaign.tenant_id == tenant_id)
    if policy_changed and not fade_changed:
        query = query.filter(Campaign.audio_policy.is_(None))

    for campaign in query.all():
        campaign.config_version = str(uuid.uuid4())
        db.add(campaign)
    db.commit()


def _after_tenant_audio_config_changed(
    db: Session,
    *,
    tenant_id: str,
    policy_changed: bool,
    fade_changed: bool,
) -> None:
    if not policy_changed and not fade_changed:
        return

    _touch_tenant_audio_campaigns(
        db,
        tenant_id=tenant_id,
        policy_changed=policy_changed,
        fade_changed=fade_changed,
    )
    devices_by_campaign = _devices_by_campaign_for_tenant(db, tenant_id=tenant_id)
    _invalidate_device_playlist_cache(set(devices_by_campaign))
    _broadcast_playlist_invalidated(
        devices_by_campaign,
        reason="tenant_audio_config_updated",
    )


def find_devices_inheriting_osd_field(
    db: Session,
    *,
    tenant_id: str,
    field_name: str,
) -> Set[str]:
    device_column = getattr(Device, OSD_DEVICE_FIELDS[field_name])
    rows = (
        db.query(Device.id)
        .filter(Device.tenant_id == tenant_id)
        .filter(device_column.is_(None))
        .all()
    )
    return {str(row.id) for row in rows}


def _devices_by_campaign_for_ids(db: Session, device_ids: Set[str]) -> Dict[str, str | None]:
    if not device_ids:
        return {}
    rows = (
        db.query(Device.id, Device.current_campaign_id)
        .filter(Device.id.in_(device_ids))
        .all()
    )
    return {
        str(row.id): str(row.current_campaign_id) if row.current_campaign_id else None
        for row in rows
    }


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


# ── SPEC 005 — Audio config ───────────────────────────────────────────────────

@router.patch("/me/audio-config", response_model=TenantResponse)
def update_my_audio_config(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
    body: TenantAudioConfigUpdate,
):
    """SPEC 005 — atualiza política de áudio e fade do tenant do usuário logado."""
    if not current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Usuário sem tenant associado")
    tenant = crud_tenant.get(db, id=str(current_user.tenant_id))
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    update_data = body.model_dump()
    policy_changed = tenant.audio_policy_default != body.audio_policy_default
    fade_changed = tenant.audio_fade_ms != body.audio_fade_ms
    tenant = crud_tenant.update(db, db_obj=tenant, obj_in=update_data)
    _after_tenant_audio_config_changed(
        db,
        tenant_id=str(tenant.id),
        policy_changed=policy_changed,
        fade_changed=fade_changed,
    )
    return tenant


@router.patch("/{tenant_id}/audio-config", response_model=TenantResponse)
def update_tenant_audio_config(
    tenant_id: str,
    *,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
    body: TenantAudioConfigUpdate,
):
    """SPEC 005 — atualiza política de áudio e fade de um tenant específico (superadmin)."""
    tenant = crud_tenant.get(db, id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    update_data = body.model_dump()
    policy_changed = tenant.audio_policy_default != body.audio_policy_default
    fade_changed = tenant.audio_fade_ms != body.audio_fade_ms
    tenant = crud_tenant.update(db, db_obj=tenant, obj_in=update_data)
    _after_tenant_audio_config_changed(
        db,
        tenant_id=str(tenant.id),
        policy_changed=policy_changed,
        fade_changed=fade_changed,
    )
    return tenant


@router.patch("/{tenant_id}/osd-config", response_model=TenantResponse)
def update_tenant_osd_config(
    tenant_id: str,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
    body: TenantOSDConfigUpdate,
):
    tenant = crud_tenant.get(db, id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant não encontrado")
    if current_user.role != "admin" and str(current_user.tenant_id) != str(tenant.id):
        raise HTTPException(status_code=403, detail="Sem permissão para atualizar este tenant")

    payload = body.model_dump()
    changed_fields = {
        field
        for field, value in payload.items()
        if _enum_value(getattr(tenant, OSD_TENANT_FIELDS[field])) != _enum_value(value)
    }
    affected_device_ids: Set[str] = set()
    for field in changed_fields:
        affected_device_ids.update(
            find_devices_inheriting_osd_field(db, tenant_id=str(tenant.id), field_name=field)
        )

    update_data = {
        OSD_TENANT_FIELDS[field]: _enum_value(value)
        for field, value in payload.items()
    }
    tenant = crud_tenant.update(db, db_obj=tenant, obj_in=update_data)

    devices_by_campaign = _devices_by_campaign_for_ids(db, affected_device_ids)
    _invalidate_device_playlist_cache(set(devices_by_campaign))
    _broadcast_playlist_invalidated(
        devices_by_campaign,
        reason="tenant_osd_config_updated",
    )
    return tenant
