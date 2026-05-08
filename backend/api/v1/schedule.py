from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from core.models import User, Campaign
from core.schemas_completos import CampaignResponse
from crud.entidades import crud_campaign

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.get("/", response_model=List[CampaignResponse])
def get_schedule(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start: Optional[datetime] = Query(None, description="Início do intervalo (ISO 8601)"),
    end: Optional[datetime] = Query(None, description="Fim do intervalo (ISO 8601)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
):
    tid = None if current_user.role == "admin" else str(current_user.tenant_id)

    if tid:
        campaigns = crud_campaign.get_by_tenant(db, tenant_id=tid)
    else:
        campaigns = crud_campaign.get_multi(db, skip=0, limit=10000)

    # Filter to campaigns that have scheduling data
    campaigns = [c for c in campaigns if c.start_date or c.end_date]

    if start:
        campaigns = [c for c in campaigns if c.end_date is None or c.end_date >= start]
    if end:
        campaigns = [c for c in campaigns if c.start_date is None or c.start_date <= end]

    return campaigns[skip: skip + limit]


@router.get("/upcoming", response_model=List[CampaignResponse])
def get_upcoming(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(7, ge=1, le=90),
):
    now = datetime.utcnow()
    future = now + timedelta(days=days)
    tid = None if current_user.role == "admin" else str(current_user.tenant_id)

    q = db.query(Campaign).filter(
        Campaign.start_date >= now,
        Campaign.start_date <= future,
    )
    if tid:
        q = q.filter(Campaign.tenant_id == tid)

    return q.order_by(Campaign.start_date).all()


@router.get("/active", response_model=List[CampaignResponse])
def get_active_now(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()
    tid = None if current_user.role == "admin" else str(current_user.tenant_id)

    q = db.query(Campaign).filter(Campaign.status == "active")
    if tid:
        q = q.filter(Campaign.tenant_id == tid)

    return q.all()
