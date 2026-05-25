from typing import List, Optional

from sqlalchemy.orm import Session

from core.models import AudioFolderTrack


ORDER_STEP = 10


class CRUDAudioFolderTrack:
    def list_by_folder(self, db: Session, *, folder_id: str) -> List[AudioFolderTrack]:
        return (
            db.query(AudioFolderTrack)
            .filter(AudioFolderTrack.folder_id == folder_id)
            .order_by(AudioFolderTrack.order_index, AudioFolderTrack.created_at)
            .all()
        )

    def get(self, db: Session, *, item_id: str) -> Optional[AudioFolderTrack]:
        return (
            db.query(AudioFolderTrack)
            .filter(AudioFolderTrack.id == item_id)
            .first()
        )

    def get_by_folder_track(
        self, db: Session, *, folder_id: str, track_id: str
    ) -> Optional[AudioFolderTrack]:
        return (
            db.query(AudioFolderTrack)
            .filter(
                AudioFolderTrack.folder_id == folder_id,
                AudioFolderTrack.track_id == track_id,
            )
            .first()
        )

    def next_order_index(self, db: Session, *, folder_id: str) -> int:
        last = (
            db.query(AudioFolderTrack)
            .filter(AudioFolderTrack.folder_id == folder_id)
            .order_by(AudioFolderTrack.order_index.desc())
            .first()
        )
        if not last:
            return 0
        return (last.order_index or 0) + ORDER_STEP

    def compact_order(self, db: Session, *, folder_id: str) -> List[AudioFolderTrack]:
        items = self.list_by_folder(db, folder_id=folder_id)
        for position, item in enumerate(items):
            expected = position * ORDER_STEP
            if item.order_index != expected:
                item.order_index = expected
                db.add(item)
        return items

    def apply_reorder(
        self,
        db: Session,
        *,
        folder_id: str,
        entries: List[dict],
    ) -> List[AudioFolderTrack]:
        by_id = {
            str(item.id): item
            for item in self.list_by_folder(db, folder_id=folder_id)
        }
        for entry in entries:
            target = by_id.get(str(entry["item_id"]))
            if target is None:
                continue
            target.order_index = int(entry["order_index"])
            db.add(target)
        db.flush()
        return self.compact_order(db, folder_id=folder_id)


crud_audio_folder_track = CRUDAudioFolderTrack()
