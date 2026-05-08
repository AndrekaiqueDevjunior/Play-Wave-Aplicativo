from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.models import DevicePairingCode, Device, Tenant
from core.schemas_completos import DevicePairingCodeCreate, DevicePairingCodeUpdate, DevicePairingCodeResponse
from .crud_base import CRUDBase
from datetime import datetime, timedelta


class CRUDDevicePairingCode(CRUDBase[DevicePairingCode, DevicePairingCodeCreate, DevicePairingCodeUpdate]):
    def get_by_code(self, db: Session, *, code: str) -> Optional[DevicePairingCode]:
        return db.query(DevicePairingCode).filter(DevicePairingCode.code == code).first()
    
    def get_by_status(self, db: Session, *, status: str) -> List[DevicePairingCode]:
        return db.query(DevicePairingCode).filter(DevicePairingCode.status == status).all()
    
    def get_active(self, db: Session) -> List[DevicePairingCode]:
        return db.query(DevicePairingCode).filter(
            and_(
                DevicePairingCode.status == "waiting",
                DevicePairingCode.expires_at > datetime.utcnow()
            )
        ).all()
    
    def get_expired(self, db: Session) -> List[DevicePairingCode]:
        return db.query(DevicePairingCode).filter(
            and_(
                DevicePairingCode.status == "waiting",
                DevicePairingCode.expires_at <= datetime.utcnow()
            )
        ).all()
    
    def get_by_device(self, db: Session, *, device_id: str) -> List[DevicePairingCode]:
        return db.query(DevicePairingCode).filter(DevicePairingCode.device_id == device_id).all()
    
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[DevicePairingCode]:
        return db.query(DevicePairingCode).filter(DevicePairingCode.tenant_id == tenant_id).all()
    
    def search(self, db: Session, *, query: str = None, skip: int = 0, limit: int = 100) -> List[DevicePairingCode]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        
        return (
            db.query(DevicePairingCode)
            .filter(
                or_(
                    DevicePairingCode.code.ilike(f"%{query}%"),
                    DevicePairingCode.player_version.ilike(f"%{query}%"),
                    DevicePairingCode.os.ilike(f"%{query}%")
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def create_code(self, db: Session, *, obj_in: DevicePairingCodeCreate) -> DevicePairingCode:
        obj_in_data = obj_in.dict()
        # Define expiração em 10 minutos
        obj_in_data["expires_at"] = datetime.utcnow() + timedelta(minutes=10)
        
        db_obj = DevicePairingCode(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_status(self, db: Session, *, db_obj: DevicePairingCode, status: str) -> DevicePairingCode:
        db_obj.status = status
        if status == "paired":
            db_obj.used_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def pair_with_device(self, db: Session, *, pairing_code: str, device_id: str, tenant_id: str) -> Optional[DevicePairingCode]:
        pairing_obj = db.query(DevicePairingCode).filter(
            and_(
                DevicePairingCode.code == pairing_code,
                DevicePairingCode.status == "waiting",
                DevicePairingCode.expires_at > datetime.utcnow()
            )
        ).first()
        
        if pairing_obj:
            pairing_obj.status = "paired"
            pairing_obj.device_id = device_id
            pairing_obj.tenant_id = tenant_id
            pairing_obj.used_at = datetime.utcnow()
            db.add(pairing_obj)
            db.commit()
            db.refresh(pairing_obj)
        
        return pairing_obj
    
    def expire_codes(self, db: Session) -> int:
        """Expira códigos que já passaram do tempo"""
        expired_codes = db.query(DevicePairingCode).filter(
            and_(
                DevicePairingCode.status == "waiting",
                DevicePairingCode.expires_at <= datetime.utcnow()
            )
        ).all()
        
        for code in expired_codes:
            code.status = "expired"
            db.add(code)
        
        db.commit()
        return len(expired_codes)
    
    def cleanup_old_codes(self, db: Session, days: int = 7) -> int:
        """Remove códigos antigos (padrão: 7 dias)"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_codes = db.query(DevicePairingCode).filter(
            DevicePairingCode.created_at < cutoff_date
        ).all()
        
        for code in old_codes:
            db.delete(code)
        
        db.commit()
        return len(old_codes)
    
    def get_statistics(self, db: Session, *, tenant_id: str = None) -> dict:
        query = db.query(DevicePairingCode)
        if tenant_id:
            query = query.filter(DevicePairingCode.tenant_id == tenant_id)
        
        total = query.count()
        waiting = query.filter(DevicePairingCode.status == "waiting").count()
        paired = query.filter(DevicePairingCode.status == "paired").count()
        expired = query.filter(DevicePairingCode.status == "expired").count()
        cancelled = query.filter(DevicePairingCode.status == "cancelled").count()
        
        return {
            "total": total,
            "waiting": waiting,
            "paired": paired,
            "expired": expired,
            "cancelled": cancelled
        }


# Instância única do CRUD
crud_device_pairing_code = CRUDDevicePairingCode(DevicePairingCode)
