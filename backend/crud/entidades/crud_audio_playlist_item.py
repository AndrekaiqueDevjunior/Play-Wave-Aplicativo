from typing import List, Optional

from sqlalchemy.orm import Session

from core.models import AudioPlaylistItem


ORDER_STEP = 10


class CRUDAudioPlaylistItem:
    def list_by_playlist(self, db: Session, *, playlist_id: str) -> List[AudioPlaylistItem]:
        return (
            db.query(AudioPlaylistItem)
            .filter(AudioPlaylistItem.playlist_id == playlist_id)
            .order_by(AudioPlaylistItem.order_index, AudioPlaylistItem.created_at)
            .all()
        )

    def get(self, db: Session, *, item_id: str) -> Optional[AudioPlaylistItem]:
        return (
            db.query(AudioPlaylistItem)
            .filter(AudioPlaylistItem.id == item_id)
            .first()
        )

    def next_order_index(self, db: Session, *, playlist_id: str) -> int:
        last = (
            db.query(AudioPlaylistItem)
            .filter(AudioPlaylistItem.playlist_id == playlist_id)
            .order_by(AudioPlaylistItem.order_index.desc())
            .first()
        )
        if not last:
            return 0
        return (last.order_index or 0) + ORDER_STEP

    def compact_order(self, db: Session, *, playlist_id: str) -> List[AudioPlaylistItem]:
        items = self.list_by_playlist(db, playlist_id=playlist_id)
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
        playlist_id: str,
        entries: List[dict],
    ) -> List[AudioPlaylistItem]:
        by_id = {
            str(item.id): item
            for item in self.list_by_playlist(db, playlist_id=playlist_id)
        }
        for entry in entries:
            target = by_id.get(str(entry["item_id"]))
            if target is None:
                continue
            target.order_index = int(entry["order_index"])
            db.add(target)
        db.flush()
        return self.compact_order(db, playlist_id=playlist_id)


crud_audio_playlist_item = CRUDAudioPlaylistItem()
