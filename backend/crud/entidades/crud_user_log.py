from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.models import UserLog, User, Tenant
from core.schemas_completos import UserLogCreate, UserLogUpdate, UserLogResponse
from .crud_base import CRUDBase


class CRUDUserLog(CRUDBase[UserLog, UserLogCreate, UserLogUpdate]):
    def get_by_target_user(self, db: Session, *, target_user_id: str) -> List[UserLog]:
        return db.query(UserLog).filter(UserLog.target_user_id == target_user_id).order_by(UserLog.created_at.desc()).all()
    
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[UserLog]:
        return db.query(UserLog).filter(UserLog.tenant_id == tenant_id).order_by(UserLog.created_at.desc()).all()
    
    def get_by_action(self, db: Session, *, action: str) -> List[UserLog]:
        return db.query(UserLog).filter(UserLog.action == action).order_by(UserLog.created_at.desc()).all()
    
    def get_by_performed_by(self, db: Session, *, performed_by: str) -> List[UserLog]:
        return db.query(UserLog).filter(UserLog.performed_by == performed_by).order_by(UserLog.created_at.desc()).all()
    
    def get_by_date_range(self, db: Session, *, start_date, end_date) -> List[UserLog]:
        return db.query(UserLog).filter(
            and_(
                UserLog.created_at >= start_date,
                UserLog.created_at <= end_date
            )
        ).order_by(UserLog.created_at.desc()).all()
    
    def search(self, db: Session, *, query: str = None, skip: int = 0, limit: int = 100) -> List[UserLog]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        
        return (
            db.query(UserLog)
            .filter(
                or_(
                    UserLog.target_user_email.ilike(f"%{query}%"),
                    UserLog.performed_by.ilike(f"%{query}%"),
                    UserLog.details.ilike(f"%{query}%")
                )
            )
            .order_by(UserLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def create_log(self, db: Session, *, target_user_id: str, action: str, performed_by: str, target_user_email: str = None, details: str = None, tenant_id: str = None) -> UserLog:
        obj_in_data = {
            "target_user_id": target_user_id,
            "action": action,
            "performed_by": performed_by,
            "target_user_email": target_user_email,
            "details": details,
            "tenant_id": tenant_id
        }
        
        db_obj = UserLog(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_statistics(self, db: Session, *, tenant_id: str = None, days: int = 7) -> dict:
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(UserLog).filter(UserLog.created_at >= cutoff_date)
        if tenant_id:
            query = query.filter(UserLog.tenant_id == tenant_id)
        
        total = query.count()
        invite = query.filter(UserLog.action == "invite").count()
        edit = query.filter(UserLog.action == "edit").count()
        activate = query.filter(UserLog.action == "activate").count()
        deactivate = query.filter(UserLog.action == "deactivate").count()
        block = query.filter(UserLog.action == "block").count()
        unblock = query.filter(UserLog.action == "unblock").count()
        reset_password = query.filter(UserLog.action == "reset_password").count()
        
        return {
            "total_logs": total,
            "by_action": {
                "invite": invite,
                "edit": edit,
                "activate": activate,
                "deactivate": deactivate,
                "block": block,
                "unblock": unblock,
                "reset_password": reset_password
            },
            "period_days": days
        }


# Instância única do CRUD
crud_user_log = CRUDUserLog(UserLog)
