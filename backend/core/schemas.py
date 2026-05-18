from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid


class TenantBase(BaseModel):
    name: str
    document: Optional[str] = None
    is_active: bool = True


class TenantCreate(TenantBase):
    pass


class Tenant(TenantBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "operator"
    is_active: bool = True
    job_title: Optional[str] = None
    account_status: str = "active"
    blocked_reason: Optional[str] = None
    last_changed_by: Optional[str] = None
    last_changed_at: Optional[datetime] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User
