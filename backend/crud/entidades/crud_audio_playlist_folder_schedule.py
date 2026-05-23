from typing import List, Optional
from fastapi.encoders import jsonable_encoder

from sqlalchemy.orm import Session

from core.models import AudioPlaylistFolderSchedule
from core.schemas_completos import (
    AudioPlaylistFolderScheduleCreate,
    AudioPlaylistFolderScheduleUpdate,
)
from .crud_base import CRUDBase


class CRUDAudioPlaylistFolderSchedule(
    CRUDBase[
        AudioPlaylistFolderSchedule,
        AudioPlaylistFolderScheduleCreate,
        AudioPlaylistFolderScheduleUpdate,
    ]
):
    def create(self, db: Session, *, obj_in: AudioPlaylistFolderScheduleCreate, playlist_id: str) -> AudioPlaylistFolderSchedule:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, playlist_id=playlist_id)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_playlist(
        self, db: Session, *, playlist_id: str
    ) -> List[AudioPlaylistFolderSchedule]:
        return (
            db.query(AudioPlaylistFolderSchedule)
            .filter(AudioPlaylistFolderSchedule.playlist_id == playlist_id)
            .all()
        )

    def get_by_folder(
        self, db: Session, *, folder_id: str
    ) -> List[AudioPlaylistFolderSchedule]:
        return (
            db.query(AudioPlaylistFolderSchedule)
            .filter(AudioPlaylistFolderSchedule.folder_id == folder_id)
            .all()
        )

    def get_active_by_playlist(
        self, db: Session, *, playlist_id: str
    ) -> List[AudioPlaylistFolderSchedule]:
        return (
            db.query(AudioPlaylistFolderSchedule)
            .filter(
                AudioPlaylistFolderSchedule.playlist_id == playlist_id,
                AudioPlaylistFolderSchedule.is_active.is_(True),
            )
            .all()
        )


crud_audio_playlist_folder_schedule = CRUDAudioPlaylistFolderSchedule(
    AudioPlaylistFolderSchedule
)
