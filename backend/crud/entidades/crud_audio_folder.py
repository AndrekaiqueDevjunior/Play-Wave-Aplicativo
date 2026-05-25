from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.models import AudioFolder
from core.schemas_completos import AudioFolderCreate, AudioFolderUpdate
from .crud_base import CRUDBase


class CRUDAudioFolder(CRUDBase[AudioFolder, AudioFolderCreate, AudioFolderUpdate]):
    def get_by_tenant(self, db: Session, *, tenant_id: str) -> List[AudioFolder]:
        return db.query(AudioFolder).filter(AudioFolder.tenant_id == tenant_id).all()

    def get_by_status(self, db: Session, *, status: str) -> List[AudioFolder]:
        return db.query(AudioFolder).filter(AudioFolder.status == status).all()

    def search(
        self,
        db: Session,
        *,
        query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AudioFolder]:
        if not query:
            return self.get_multi(db, skip=skip, limit=limit)
        like = f"%{query}%"
        return (
            db.query(AudioFolder)
            .filter(or_(AudioFolder.name.ilike(like), AudioFolder.description.ilike(like)))
            .offset(skip)
            .limit(limit)
            .all()
        )


crud_audio_folder = CRUDAudioFolder(AudioFolder)
