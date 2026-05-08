from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.models import Location, Device, Tenant
from core.schemas_completos import LocationCreate, LocationUpdate, LocationResponse
from .crud_base import CRUDBase


class CRUDLocation(CRUDBase[Location, LocationCreate, LocationUpdate]):
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[Location]:
        return db.query(Location).filter(Location.tenant_id == tenant_id).all()
    
    def get_by_name(self, db: Session, *, name: str) -> Optional[Location]:
        return db.query(Location).filter(Location.name == name).first()
    
    def get_by_address(self, db: Session, *, address: str) -> List[Location]:
        return db.query(Location).filter(Location.address.ilike(f"%{address}%")).all()
    
    def get_with_devices(self, db: Session, *, location_id: str) -> Optional[Location]:
        location = db.query(Location).filter(Location.id == location_id).first()
        if location:
            location.devices = db.query(Device).filter(Device.location == location.name).all()
        return location
    
    def update_device_count(self, db: Session, *, location_id: str) -> Location:
        location = db.query(Location).filter(Location.id == location_id).first()
        if location:
            device_count = db.query(Device).filter(Device.location == location.name).count()
            location.device_count = device_count
            db.add(location)
            db.commit()
            db.refresh(location)
        return location
    
    def search(self, db: Session, *, query: str = None, skip: int = 0, limit: int = 100) -> List[Location]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        
        return (
            db.query(Location)
            .filter(
                or_(
                    Location.name.ilike(f"%{query}%"),
                    Location.description.ilike(f"%{query}%"),
                    Location.address.ilike(f"%{query}%")
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_device_count_for_all(self, db: Session) -> List[Location]:
        locations = db.query(Location).all()
        for location in locations:
            location.device_count = db.query(Device).filter(Device.location == location.name).count()
        return locations


# Instância única do CRUD
crud_location = CRUDLocation(Location)
