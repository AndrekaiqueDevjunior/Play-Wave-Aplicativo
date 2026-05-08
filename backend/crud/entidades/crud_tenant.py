from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.models import Tenant
from core.schemas_completos import TenantCreate, TenantUpdate, TenantResponse
from .crud_base import CRUDBase


class CRUDTenant(CRUDBase[Tenant, TenantCreate, TenantUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Tenant]:
        return db.query(Tenant).filter(Tenant.name == name).first()
    
    def get_by_document(self, db: Session, *, document: str) -> Optional[Tenant]:
        return db.query(Tenant).filter(Tenant.document == document).first()
    
    def get_active(self, db: Session) -> List[Tenant]:
        return db.query(Tenant).filter(Tenant.is_active == True).all()
    
    def get_multi_by_plan(self, db: Session, *, plan: str) -> List[Tenant]:
        return db.query(Tenant).filter(Tenant.plan == plan).all()
    
    def search(self, db: Session, *, query: str = None, skip: int = 0, limit: int = 100) -> List[Tenant]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        
        return (
            db.query(Tenant)
            .filter(
                or_(
                    Tenant.name.ilike(f"%{query}%"),
                    Tenant.document.ilike(f"%{query}%"),
                    Tenant.contact_email.ilike(f"%{query}%")
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )


# Instância única do CRUD
crud_tenant = CRUDTenant(Tenant)
