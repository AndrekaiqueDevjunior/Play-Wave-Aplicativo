from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.models import Device, Campaign, AudioPlaylist
from core.schemas_completos import DeviceCreate, DeviceUpdate, DeviceResponse
from .crud_base import CRUDBase


class CRUDDevice(CRUDBase[Device, DeviceCreate, DeviceUpdate]):
    def create(self, db: Session, *, obj_in: DeviceCreate) -> Device:
        obj_in_data = obj_in.model_dump()
        # Limpar strings vazias para campos UUID
        if obj_in_data.get("audio_playlist_id") == "" or obj_in_data.get("audio_playlist_id") is None:
            obj_in_data["audio_playlist_id"] = None
        if obj_in_data.get("current_campaign_id") == "" or obj_in_data.get("current_campaign_id") is None:
            obj_in_data["current_campaign_id"] = None
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_pairing_code(self, db: Session, *, pairing_code: str) -> Optional[Device]:
        return db.query(Device).filter(Device.pairing_code == pairing_code).first()
    
    def get_by_device_token(self, db: Session, *, device_token: str) -> Optional[Device]:
        return db.query(Device).filter(Device.device_token == device_token).first()
    
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[Device]:
        return db.query(Device).filter(Device.tenant_id == tenant_id).all()
    
    def get_by_status(self, db: Session, *, status: str) -> List[Device]:
        return db.query(Device).filter(Device.status == status).all()
    
    def get_by_type(self, db: Session, *, device_type: str) -> List[Device]:
        return db.query(Device).filter(Device.device_type == device_type).all()
    
    def get_by_location(self, db: Session, *, location: str) -> List[Device]:
        return db.query(Device).filter(Device.location.ilike(f"%{location}%")).all()
    
    def get_by_group(self, db: Session, *, group: str) -> List[Device]:
        return db.query(Device).filter(Device.group.ilike(f"%{group}%")).all()
    
    def get_active(self, db: Session) -> List[Device]:
        return db.query(Device).filter(Device.is_active == True).all()
    
    def get_online(self, db: Session) -> List[Device]:
        return db.query(Device).filter(Device.status == "online").all()
    
    def get_offline(self, db: Session) -> List[Device]:
        return db.query(Device).filter(Device.status == "offline").all()
    
    def get_waiting_pairing(self, db: Session) -> List[Device]:
        return db.query(Device).filter(Device.status == "waiting_pairing").all()
    
    def get_by_campaign(self, db: Session, *, campaign_id: str) -> List[Device]:
        return db.query(Device).filter(Device.current_campaign_id == campaign_id).all()
    
    def get_by_audio_playlist(self, db: Session, *, playlist_id: str) -> List[Device]:
        return db.query(Device).filter(Device.audio_playlist_id == playlist_id).all()
    
    def search(self, db: Session, *, query: str = None, skip: int = 0, limit: int = 100) -> List[Device]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        
        return (
            db.query(Device)
            .filter(
                or_(
                    Device.name.ilike(f"%{query}%"),
                    Device.pairing_code.ilike(f"%{query}%"),
                    Device.location.ilike(f"%{query}%"),
                    Device.group.ilike(f"%{query}%"),
                    Device.ip_address.ilike(f"%{query}%")
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def update_status(self, db: Session, *, db_obj: Device, status: str) -> Device:
        db_obj.status = status
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_campaign(self, db: Session, *, db_obj: Device, campaign_id: str, campaign_name: str = None) -> Device:
        db_obj.current_campaign_id = campaign_id
        if campaign_name:
            db_obj.current_campaign = campaign_name
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_last_seen(self, db: Session, *, db_obj: Device, ip_address: str = None) -> Device:
        from datetime import datetime
        db_obj.last_seen_at = datetime.utcnow()
        if ip_address:
            db_obj.ip_address = ip_address
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def block_device(self, db: Session, *, db_obj: Device) -> Device:
        db_obj.is_blocked = True
        db_obj.status = "blocked"
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def unblock_device(self, db: Session, *, db_obj: Device) -> Device:
        db_obj.is_blocked = False
        db_obj.status = "online"
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_statistics(self, db: Session, *, tenant_id: str = None) -> dict:
        query = db.query(Device)
        if tenant_id:
            query = query.filter(Device.tenant_id == tenant_id)
        
        total = query.count()
        online = query.filter(Device.status == "online").count()
        offline = query.filter(Device.status == "offline").count()
        syncing = query.filter(Device.status == "syncing").count()
        error = query.filter(Device.status == "error").count()
        blocked = query.filter(Device.is_blocked == True).count()
        
        return {
            "total": total,
            "online": online,
            "offline": offline,
            "syncing": syncing,
            "error": error,
            "blocked": blocked
        }


# Instância única do CRUD
crud_device = CRUDDevice(Device)
