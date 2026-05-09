from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, cast
from sqlalchemy.dialects.postgresql import JSONB
from core.models import Campaign, Device, Media
from core.schemas_completos import CampaignCreate, CampaignUpdate, CampaignResponse
from .crud_base import CRUDBase


class CRUDCampaign(CRUDBase[Campaign, CampaignCreate, CampaignUpdate]):
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[Campaign]:
        return db.query(Campaign).filter(Campaign.tenant_id == tenant_id).all()
    
    def get_by_status(self, db: Session, *, status: str) -> List[Campaign]:
        return db.query(Campaign).filter(Campaign.status == status).all()
    
    def get_active(self, db: Session) -> List[Campaign]:
        return db.query(Campaign).filter(Campaign.status == "active").all()
    
    def get_scheduled(self, db: Session) -> List[Campaign]:
        return db.query(Campaign).filter(Campaign.status == "scheduled").all()
    
    def get_by_priority(self, db: Session, *, priority_min: int = 1, priority_max: int = 10) -> List[Campaign]:
        return db.query(Campaign).filter(
            and_(Campaign.priority >= priority_min, Campaign.priority <= priority_max)
        ).order_by(Campaign.priority.desc()).all()
    
    def get_by_date_range(self, db: Session, *, start_date, end_date) -> List[Campaign]:
        return db.query(Campaign).filter(
            and_(
                Campaign.start_date <= start_date,
                Campaign.end_date >= end_date
            )
        ).all()
    
    def get_by_device(self, db: Session, *, device_id: str) -> List[Campaign]:
        return db.query(Campaign).filter(
            cast(Campaign.device_ids, JSONB).contains([device_id])
        ).all()

    def get_active_for_device(self, db: Session, *, device_id: str) -> Optional[Campaign]:
        """Return the highest-priority active campaign that targets this device."""
        return (
            db.query(Campaign)
            .filter(
                and_(
                    cast(Campaign.device_ids, JSONB).contains([device_id]),
                    Campaign.status == "active",
                )
            )
            .order_by(Campaign.priority.desc())
            .first()
        )
    
    def get_by_media(self, db: Session, *, media_id: str) -> List[Campaign]:
        return db.query(Campaign).filter(
            cast(Campaign.media_ids, JSONB).contains([media_id])
        ).all()
    
    def search(self, db: Session, *, query: str = None, skip: int = 0, limit: int = 100) -> List[Campaign]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        
        return (
            db.query(Campaign)
            .filter(
                or_(
                    Campaign.name.ilike(f"%{query}%"),
                    Campaign.description.ilike(f"%{query}%")
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def update_status(self, db: Session, *, db_obj: Campaign, status: str) -> Campaign:
        db_obj.status = status
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def increment_views(self, db: Session, *, campaign_id: str) -> Campaign:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if campaign:
            campaign.total_views = (campaign.total_views or 0) + 1
            db.add(campaign)
            db.commit()
            db.refresh(campaign)
        return campaign
    
    def get_statistics(self, db: Session, *, tenant_id: str = None) -> dict:
        query = db.query(Campaign)
        if tenant_id:
            query = query.filter(Campaign.tenant_id == tenant_id)
        
        total = query.count()
        draft = query.filter(Campaign.status == "draft").count()
        scheduled = query.filter(Campaign.status == "scheduled").count()
        active = query.filter(Campaign.status == "active").count()
        paused = query.filter(Campaign.status == "paused").count()
        ended = query.filter(Campaign.status == "ended").count()
        
        return {
            "total": total,
            "draft": draft,
            "scheduled": scheduled,
            "active": active,
            "paused": paused,
            "ended": ended
        }


# Instância única do CRUD
crud_campaign = CRUDCampaign(Campaign)
