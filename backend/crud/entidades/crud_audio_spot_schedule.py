from typing import List, Optional
from fastapi.encoders import jsonable_encoder

from sqlalchemy.orm import Session

from core.models import AudioSpotSchedule
from core.schemas_completos import (
    AudioSpotScheduleCreate,
    AudioSpotScheduleUpdate,
)
from .crud_base import CRUDBase


class CRUDAudioSpotSchedule(
    CRUDBase[
        AudioSpotSchedule,
        AudioSpotScheduleCreate,
        AudioSpotScheduleUpdate,
    ]
):
    def create(self, db: Session, *, obj_in: AudioSpotScheduleCreate, playlist_id: str) -> AudioSpotSchedule:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, playlist_id=playlist_id)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_playlist(
        self, db: Session, *, playlist_id: str
    ) -> List[AudioSpotSchedule]:
        return (
            db.query(AudioSpotSchedule)
            .filter(AudioSpotSchedule.playlist_id == playlist_id)
            .all()
        )

    def get_by_spot(
        self, db: Session, *, spot_id: str
    ) -> List[AudioSpotSchedule]:
        return (
            db.query(AudioSpotSchedule)
            .filter(AudioSpotSchedule.spot_id == spot_id)
            .all()
        )

    def get_active_by_playlist(
        self, db: Session, *, playlist_id: str
    ) -> List[AudioSpotSchedule]:
        return (
            db.query(AudioSpotSchedule)
            .filter(
                AudioSpotSchedule.playlist_id == playlist_id,
                AudioSpotSchedule.is_active.is_(True),
            )
            .all()
        )


crud_audio_spot_schedule = CRUDAudioSpotSchedule(AudioSpotSchedule)
