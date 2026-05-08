from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.models import DeviceEvent, Device, Tenant
from core.schemas_completos import DeviceEventCreate, DeviceEventUpdate, DeviceEventResponse
from .crud_base import CRUDBase


class CRUDDeviceEvent(CRUDBase[DeviceEvent, DeviceEventCreate, DeviceEventUpdate]):
    def get_by_device(self, db: Session, *, device_id: str) -> List[DeviceEvent]:
        return db.query(DeviceEvent).filter(DeviceEvent.device_id == device_id).order_by(DeviceEvent.created_at.desc()).all()
    
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[DeviceEvent]:
        return db.query(DeviceEvent).filter(DeviceEvent.tenant_id == tenant_id).order_by(DeviceEvent.created_at.desc()).all()
    
    def get_by_event_type(self, db: Session, *, event_type: str) -> List[DeviceEvent]:
        return db.query(DeviceEvent).filter(DeviceEvent.event_type == event_type).order_by(DeviceEvent.created_at.desc()).all()
    
    def get_by_severity(self, db: Session, *, severity: str) -> List[DeviceEvent]:
        return db.query(DeviceEvent).filter(DeviceEvent.severity == severity).order_by(DeviceEvent.created_at.desc()).all()
    
    def get_critical(self, db: Session) -> List[DeviceEvent]:
        return db.query(DeviceEvent).filter(DeviceEvent.severity == "critical").order_by(DeviceEvent.created_at.desc()).all()
    
    def get_errors(self, db: Session) -> List[DeviceEvent]:
        return db.query(DeviceEvent).filter(DeviceEvent.severity == "error").order_by(DeviceEvent.created_at.desc()).all()
    
    def get_by_date_range(self, db: Session, *, start_date, end_date) -> List[DeviceEvent]:
        return db.query(DeviceEvent).filter(
            and_(
                DeviceEvent.created_at >= start_date,
                DeviceEvent.created_at <= end_date
            )
        ).order_by(DeviceEvent.created_at.desc()).all()
    
    def search(self, db: Session, *, query: str = None, skip: int = 0, limit: int = 100) -> List[DeviceEvent]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        
        return (
            db.query(DeviceEvent)
            .filter(
                or_(
                    DeviceEvent.device_name.ilike(f"%{query}%"),
                    DeviceEvent.description.ilike(f"%{query}%")
                )
            )
            .order_by(DeviceEvent.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def create_event(self, db: Session, *, device_id: str, event_type: str, description: str = None, severity: str = "info", metadata: dict = None, device_name: str = None) -> DeviceEvent:
        obj_in_data = {
            "device_id": device_id,
            "event_type": event_type,
            "description": description,
            "severity": severity,
            "metadata": metadata,
            "device_name": device_name
        }
        
        db_obj = DeviceEvent(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_statistics(self, db: Session, *, tenant_id: str = None, days: int = 7) -> dict:
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(DeviceEvent).filter(DeviceEvent.created_at >= cutoff_date)
        if tenant_id:
            query = query.filter(DeviceEvent.tenant_id == tenant_id)
        
        total = query.count()
        critical = query.filter(DeviceEvent.severity == "critical").count()
        error = query.filter(DeviceEvent.severity == "error").count()
        warning = query.filter(DeviceEvent.severity == "warning").count()
        info = query.filter(DeviceEvent.severity == "info").count()
        
        # Estatísticas por tipo de evento
        paired = query.filter(DeviceEvent.event_type == "paired").count()
        blocked = query.filter(DeviceEvent.event_type == "blocked").count()
        offline_detected = query.filter(DeviceEvent.event_type == "offline_detected").count()
        media_error = query.filter(DeviceEvent.event_type == "media_error").count()
        
        return {
            "total": total,
            "by_severity": {
                "critical": critical,
                "error": error,
                "warning": warning,
                "info": info
            },
            "by_event_type": {
                "paired": paired,
                "blocked": blocked,
                "offline_detected": offline_detected,
                "media_error": media_error
            }
        }


# Instância única do CRUD
crud_device_event = CRUDDeviceEvent(DeviceEvent)
