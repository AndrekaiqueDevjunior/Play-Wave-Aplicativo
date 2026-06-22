from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.models import User, Tenant
from core.schemas_completos import UserCreate, UserUpdate, UserResponse
from .crud_base import CRUDBase


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[User]:
        return db.query(User).filter(User.tenant_id == tenant_id).all()
    
    def get_by_role(self, db: Session, *, role: str) -> List[User]:
        return db.query(User).filter(User.role == role).all()
    
    def get_active(self, db: Session) -> List[User]:
        return db.query(User).filter(User.is_active == True).all()
    
    def get_by_tenant_and_role(self, db: Session, *, tenant_id: str, role: str) -> List[User]:
        return (
            db.query(User)
            .filter(and_(User.tenant_id == tenant_id, User.role == role))
            .all()
        )
    
    def search(self, db: Session, *, query: str = None, skip: int = 0, limit: int = 100) -> List[User]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        
        return (
            db.query(User)
            .filter(
                or_(
                    User.name.ilike(f"%{query}%"),
                    User.email.ilike(f"%{query}%")
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def email_exists(self, db: Session, *, email: str) -> bool:
        return db.query(User).filter(User.email == email).first() is not None

    def get_by_invite_token(self, db: Session, *, token: str) -> Optional[User]:
        return db.query(User).filter(User.invite_token == token).first()

    def get_by_password_reset_token(self, db: Session, *, token: str) -> Optional[User]:
        return db.query(User).filter(User.password_reset_token == token).first()

    def create_with_tenant(self, db: Session, *, obj_in: UserCreate, tenant_id: str) -> User:
        obj_in_data = obj_in.dict()
        obj_in_data["tenant_id"] = tenant_id
        db_obj = User(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


# Instância única do CRUD
crud_user = CRUDUser(User)
