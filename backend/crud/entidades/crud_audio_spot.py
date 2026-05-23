from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.models import AudioSpot
from core.schemas_completos import AudioSpotCreate, AudioSpotUpdate
from .crud_base import CRUDBase


class CRUDAudioSpot(CRUDBase[AudioSpot, AudioSpotCreate, AudioSpotUpdate]):
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[AudioSpot]:
        return db.query(AudioSpot).filter(AudioSpot.tenant_id == tenant_id).all()

    def get_by_status(self, db: Session, *, status: str) -> List[AudioSpot]:
        return db.query(AudioSpot).filter(AudioSpot.status == status).all()

    def search(
        self,
        db: Session,
        *,
        query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AudioSpot]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        like = f"%{query}%"
        return (
            db.query(AudioSpot)
            .filter(or_(AudioSpot.name.ilike(like), AudioSpot.description.ilike(like)))
            .offset(skip)
            .limit(limit)
            .all()
        )


crud_audio_spot = CRUDAudioSpot(AudioSpot)
