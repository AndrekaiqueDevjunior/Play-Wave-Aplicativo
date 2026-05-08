from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def get_multi_by_ids(
        self, db: Session, ids: List[Any]
    ) -> List[ModelType]:
        return db.query(self.model).filter(self.model.id.in_(ids)).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Any) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj

    def count(self, db: Session) -> int:
        return db.query(self.model).count()

    def exists(self, db: Session, *, id: Any) -> bool:
        return db.query(self.model).filter(self.model.id == id).first() is not None

    def search(
        self,
        db: Session,
        *,
        query: str = None,
        skip: int = 0,
        limit: int = 100,
        search_fields: List[str] = None
    ) -> List[ModelType]:
        if not query or not search_fields:
            return self.get_multi(db, skip=skip, limit=limit)
        
        filters = []
        for field in search_fields:
            filters.append(getattr(self.model, field).ilike(f"%{query}%"))
        
        return (
            db.query(self.model)
            .filter(or_(*filters))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_field(self, db: Session, *, field_name: str, value: Any) -> Optional[ModelType]:
        field = getattr(self.model, field_name)
        return db.query(self.model).filter(field == value).first()

    def get_multi_by_field(
        self, db: Session, *, field_name: str, value: Any
    ) -> List[ModelType]:
        field = getattr(self.model, field_name)
        return db.query(self.model).filter(field == value).all()

    def get_active(self, db: Session) -> List[ModelType]:
        """Retorna apenas registros ativos (se tiver campo is_active)"""
        if hasattr(self.model, 'is_active'):
            return db.query(self.model).filter(self.model.is_active == True).all()
        return self.get_multi(db)
