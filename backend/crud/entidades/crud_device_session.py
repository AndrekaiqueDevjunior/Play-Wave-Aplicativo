from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.models import DeviceSession, Device, Tenant
from core.schemas_completos import DeviceSessionCreate, DeviceSessionUpdate, DeviceSessionResponse
from .crud_base import CRUDBase
from datetime import datetime, timedelta


class CRUDDeviceSession(CRUDBase[DeviceSession, DeviceSessionCreate, DeviceSessionUpdate]):
    def get_by_token(self, db: Session, *, token: str) -> Optional[DeviceSession]:
        return db.query(DeviceSession).filter(DeviceSession.token == token).first()
    
    def get_by_device(self, db: Session, *, device_id: str) -> List[DeviceSession]:
        return db.query(DeviceSession).filter(DeviceSession.device_id == device_id).all()
    
    def get_active_by_device(self, db: Session, *, device_id: str) -> Optional[DeviceSession]:
        return db.query(DeviceSession).filter(
            and_(
                DeviceSession.device_id == device_id,
                DeviceSession.is_active == True,
                DeviceSession.expires_at > datetime.utcnow()
            )
        ).first()
    
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[DeviceSession]:
        return db.query(DeviceSession).filter(DeviceSession.tenant_id == tenant_id).all()
    
    def get_active(self, db: Session) -> List[DeviceSession]:
        return db.query(DeviceSession).filter(
            and_(
                DeviceSession.is_active == True,
                DeviceSession.expires_at > datetime.utcnow()
            )
        ).all()
    
    def get_expired(self, db: Session) -> List[DeviceSession]:
        return db.query(DeviceSession).filter(
            and_(
                DeviceSession.is_active == True,
                DeviceSession.expires_at <= datetime.utcnow()
            )
        ).all()
    
    def search(self, db: Session, *, query: str = None, skip: int = 0, limit: int = 100) -> List[DeviceSession]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        
        return (
            db.query(DeviceSession)
            .filter(
                or_(
                    DeviceSession.token.ilike(f"%{query}%")
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def create_session(self, db: Session, *, obj_in: DeviceSessionCreate) -> DeviceSession:
        obj_in_data = obj_in.dict()
        # Define expiração padrão de 30 dias
        if "expires_at" not in obj_in_data:
            obj_in_data["expires_at"] = datetime.utcnow() + timedelta(days=30)
        
        db_obj = DeviceSession(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def revoke_session(self, db: Session, *, session_id: str) -> Optional[DeviceSession]:
        session = db.query(DeviceSession).filter(DeviceSession.id == session_id).first()
        if session:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            db.add(session)
            db.commit()
            db.refresh(session)
        return session
    
    def revoke_all_device_sessions(self, db: Session, *, device_id: str) -> int:
        sessions = db.query(DeviceSession).filter(
            and_(
                DeviceSession.device_id == device_id,
                DeviceSession.is_active == True
            )
        ).all()
        
        for session in sessions:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            db.add(session)
        
        db.commit()
        return len(sessions)
    
    def update_last_used(self, db: Session, *, session_id: str) -> Optional[DeviceSession]:
        session = db.query(DeviceSession).filter(DeviceSession.id == session_id).first()
        if session:
            session.last_used_at = datetime.utcnow()
            db.add(session)
            db.commit()
            db.refresh(session)
        return session
    
    def cleanup_expired_sessions(self, db: Session) -> int:
        """Remove sessões expiradas"""
        expired_sessions = db.query(DeviceSession).filter(
            and_(
                DeviceSession.is_active == True,
                DeviceSession.expires_at <= datetime.utcnow()
            )
        ).all()
        
        for session in expired_sessions:
            session.is_active = False
            db.add(session)
        
        db.commit()
        return len(expired_sessions)
    
    def get_statistics(self, db: Session, *, tenant_id: str = None) -> dict:
        query = db.query(DeviceSession)
        if tenant_id:
            query = query.filter(DeviceSession.tenant_id == tenant_id)
        
        total = query.count()
        active = query.filter(
            and_(
                DeviceSession.is_active == True,
                DeviceSession.expires_at > datetime.utcnow()
            )
        ).count()
        expired = query.filter(
            and_(
                DeviceSession.is_active == False,
                DeviceSession.revoked_at.isnot(None)
            )
        ).count()
        
        return {
            "total": total,
            "active": active,
            "expired": expired
        }


# Instância única do CRUD
crud_device_session = CRUDDeviceSession(DeviceSession)
