from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from core.models import User, Device, DeviceEvent
from core.schemas_completos import DeviceResponse
from crud.entidades import crud_device, crud_device_event

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/devices", response_model=List[DeviceResponse])
def get_device_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    tid = None if current_user.role == "admin" else str(current_user.tenant_id)

    if status:
        devices = crud_device.get_by_status(db, status=status)
    elif tid:
        devices = crud_device.get_by_tenant(db, tenant_id=tid)
    else:
        devices = crud_device.get_multi(db, skip=skip, limit=limit)

    if tid:
        devices = [d for d in devices if str(d.tenant_id) == tid]

    return devices[skip: skip + limit]


@router.get("/stats")
def get_monitoring_stats(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = None if current_user.role == "admin" else str(current_user.tenant_id)
    return crud_device.get_statistics(db, tenant_id=tid)


@router.get("/events")
def get_events(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    device_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    tid = None if current_user.role == "admin" else str(current_user.tenant_id)

    if device_id:
        events = crud_device_event.get_by_device(db, device_id=device_id)
    elif tid:
        events = crud_device_event.get_by_tenant(db, tenant_id=tid)
    else:
        events = crud_device_event.get_multi(db, skip=skip, limit=limit)

    return events[skip: skip + limit]


@router.get("/events/{device_id}")
def get_device_events(
    device_id: str,
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
):
    events = crud_device_event.get_by_device(db, device_id=device_id)
    return events[skip: skip + limit]
