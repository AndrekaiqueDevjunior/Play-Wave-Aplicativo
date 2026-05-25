from typing import List, Optional

from sqlalchemy.orm import Session

from core.models import CampaignPlaylistItem


ORDER_STEP = 10


class CRUDCampaignPlaylistItem:
    """CRUD helpers for campaign_playlist_items.

    The order_index is stored in increments of ORDER_STEP so inserts/moves
    between two items don't require rewriting every row. We compact the
    sequence (0, 10, 20, ...) only when needed (e.g., after a reorder payload).
    """

    def list_by_campaign(self, db: Session, *, campaign_id: str) -> List[CampaignPlaylistItem]:
        return (
            db.query(CampaignPlaylistItem)
            .filter(CampaignPlaylistItem.campaign_id == campaign_id)
            .order_by(CampaignPlaylistItem.order_index, CampaignPlaylistItem.created_at)
            .all()
        )

    def get(self, db: Session, *, item_id: str) -> Optional[CampaignPlaylistItem]:
        return (
            db.query(CampaignPlaylistItem)
            .filter(CampaignPlaylistItem.id == item_id)
            .first()
        )

    def next_order_index(self, db: Session, *, campaign_id: str) -> int:
        last = (
            db.query(CampaignPlaylistItem)
            .filter(CampaignPlaylistItem.campaign_id == campaign_id)
            .order_by(CampaignPlaylistItem.order_index.desc())
            .first()
        )
        if not last:
            return 0
        return (last.order_index or 0) + ORDER_STEP

    def compact_order(self, db: Session, *, campaign_id: str) -> List[CampaignPlaylistItem]:
        items = self.list_by_campaign(db, campaign_id=campaign_id)
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
        campaign_id: str,
        entries: List[dict],
    ) -> List[CampaignPlaylistItem]:
        """Apply a reorder payload then compact to canonical 0/10/20 spacing.

        entries: list of {item_id, order_index}. Items not listed keep their
        current order_index relative to the rest.
        """
        by_id = {
            str(item.id): item
            for item in self.list_by_campaign(db, campaign_id=campaign_id)
        }
        for entry in entries:
            target = by_id.get(str(entry["item_id"]))
            if target is None:
                continue
            target.order_index = int(entry["order_index"])
            db.add(target)
        db.flush()
        return self.compact_order(db, campaign_id=campaign_id)


crud_campaign_playlist_item = CRUDCampaignPlaylistItem()
