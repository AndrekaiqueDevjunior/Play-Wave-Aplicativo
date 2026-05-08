from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from core.models import PlaybackLog, Device, Campaign, Media, Tenant
from core.schemas_completos import PlaybackLogCreate, PlaybackLogUpdate, PlaybackLogResponse
from .crud_base import CRUDBase


class CRUDPlaybackLog(CRUDBase[PlaybackLog, PlaybackLogCreate, PlaybackLogUpdate]):
    def get_by_device(self, db: Session, *, device_id: str) -> List[PlaybackLog]:
        return db.query(PlaybackLog).filter(PlaybackLog.device_id == device_id).order_by(PlaybackLog.created_at.desc()).all()
    
    def get_by_campaign(self, db: Session, *, campaign_id: str) -> List[PlaybackLog]:
        return db.query(PlaybackLog).filter(PlaybackLog.campaign_id == campaign_id).order_by(PlaybackLog.created_at.desc()).all()
    
    def get_by_media(self, db: Session, *, media_id: str) -> List[PlaybackLog]:
        return db.query(PlaybackLog).filter(PlaybackLog.media_id == media_id).order_by(PlaybackLog.created_at.desc()).all()
    
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[PlaybackLog]:
        return db.query(PlaybackLog).filter(PlaybackLog.tenant_id == tenant_id).order_by(PlaybackLog.created_at.desc()).all()
    
    def get_by_status(self, db: Session, *, status: str) -> List[PlaybackLog]:
        return db.query(PlaybackLog).filter(PlaybackLog.status == status).order_by(PlaybackLog.created_at.desc()).all()
    
    def get_by_date_range(self, db: Session, *, start_date, end_date) -> List[PlaybackLog]:
        return db.query(PlaybackLog).filter(
            and_(
                PlaybackLog.created_at >= start_date,
                PlaybackLog.created_at <= end_date
            )
        ).order_by(PlaybackLog.created_at.desc()).all()
    
    def get_completed(self, db: Session) -> List[PlaybackLog]:
        return db.query(PlaybackLog).filter(PlaybackLog.status == "completed").order_by(PlaybackLog.created_at.desc()).all()
    
    def get_interrupted(self, db: Session) -> List[PlaybackLog]:
        return db.query(PlaybackLog).filter(PlaybackLog.status == "interrupted").order_by(PlaybackLog.created_at.desc()).all()
    
    def get_with_errors(self, db: Session) -> List[PlaybackLog]:
        return db.query(PlaybackLog).filter(PlaybackLog.status == "error").order_by(PlaybackLog.created_at.desc()).all()
    
    def search(self, db: Session, *, query: str = None, skip: int = 0, limit: int = 100) -> List[PlaybackLog]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        
        return (
            db.query(PlaybackLog)
            .filter(
                or_(
                    PlaybackLog.device_name.ilike(f"%{query}%"),
                    PlaybackLog.campaign_name.ilike(f"%{query}%"),
                    PlaybackLog.media_name.ilike(f"%{query}%")
                )
            )
            .order_by(PlaybackLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def create_log(self, db: Session, *, device_id: str, campaign_id: str, media_id: str, started_at=None, ended_at=None, duration_ms=None, status="completed") -> PlaybackLog:
        obj_in_data = {
            "device_id": device_id,
            "campaign_id": campaign_id,
            "media_id": media_id,
            "started_at": started_at,
            "ended_at": ended_at,
            "duration_ms": duration_ms,
            "status": status
        }
        
        db_obj = PlaybackLog(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_statistics(self, db: Session, *, tenant_id: str = None, days: int = 7) -> dict:
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(PlaybackLog).filter(PlaybackLog.created_at >= cutoff_date)
        if tenant_id:
            query = query.filter(PlaybackLog.tenant_id == tenant_id)
        
        total = query.count()
        completed = query.filter(PlaybackLog.status == "completed").count()
        interrupted = query.filter(PlaybackLog.status == "interrupted").count()
        error = query.filter(PlaybackLog.status == "error").count()
        
        # Total de tempo reproduzido
        total_duration = query.with_entities(func.sum(PlaybackLog.duration_ms)).scalar() or 0
        
        # Dispositivos únicos
        unique_devices = query.with_entities(func.count(func.distinct(PlaybackLog.device_id))).scalar() or 0
        
        # Campanhas únicas
        unique_campaigns = query.with_entities(func.count(func.distinct(PlaybackLog.campaign_id))).scalar() or 0
        
        # Mídias únicas
        unique_media = query.with_entities(func.count(func.distinct(PlaybackLog.media_id))).scalar() or 0
        
        return {
            "total": total,
            "completed": completed,
            "interrupted": interrupted,
            "error": error,
            "total_duration_ms": total_duration,
            "unique_devices": unique_devices,
            "unique_campaigns": unique_campaigns,
            "unique_media": unique_media
        }


# Instância única do CRUD
crud_playback_log = CRUDPlaybackLog(PlaybackLog)
