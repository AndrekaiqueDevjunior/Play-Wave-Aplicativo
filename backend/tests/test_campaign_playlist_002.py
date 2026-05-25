import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from api.v1.devices import _build_media_payload
from crud.entidades.crud_campaign_playlist_item import crud_campaign_playlist_item
from core.models import Media


def _item(item_id, order_index, *, is_active=True, repeat_count=1):
    return SimpleNamespace(
        id=item_id,
        campaign_id="campaign-1",
        media_id=f"media-{item_id}",
        order_index=order_index,
        created_at=datetime(2026, 5, 23, 8, order_index),
        display_duration_seconds=None,
        starts_at=None,
        ends_at=None,
        is_active=is_active,
        repeat_count=repeat_count,
    )


def _media(media_id, name, media_type="image", duration=15):
    return SimpleNamespace(
        id=media_id,
        name=name,
        type=media_type,
        file_url=f"/uploads/{media_id}.dat",
        thumbnail_url=None,
        duration=duration,
        duration_seconds=None,
        display_duration_seconds=None,
        file_version=1,
        file_hash=None,
        mime_type=None,
        status="available",
        is_active=True,
        starts_at=None,
        ends_at=None,
        audio_policy=None,
        has_audio=None,
    )


class FakePlaylistQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def all(self):
        return sorted(self.rows, key=lambda row: (row.order_index, row.created_at))

    def first(self):
        ordered = self.all()
        return ordered[-1] if ordered else None


class FakePlaylistSession:
    def __init__(self, rows):
        self.rows = rows

    def query(self, _model):
        return FakePlaylistQuery(self.rows)

    def add(self, _obj):
        return None

    def flush(self):
        return None


class FakeMediaQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *_args, **_kwargs):
        return self

    def all(self):
        return self.rows


class FakeMediaSession:
    def __init__(self, rows):
        self.rows = rows

    def query(self, model):
        if model is not Media:
            raise AssertionError(f"Unexpected query model: {model!r}")
        return FakeMediaQuery(self.rows)


class CampaignPlaylistOrderTest(unittest.TestCase):
    def test_apply_reorder_persists_compacted_order(self):
        first = _item("a", 0)
        second = _item("b", 10)
        third = _item("c", 20)
        db = FakePlaylistSession([first, second, third])

        result = crud_campaign_playlist_item.apply_reorder(
            db,
            campaign_id="campaign-1",
            entries=[
                {"item_id": "c", "order_index": 0},
                {"item_id": "a", "order_index": 10},
                {"item_id": "b", "order_index": 20},
            ],
        )

        self.assertEqual([item.id for item in result], ["c", "a", "b"])
        self.assertEqual(
            [(item.id, item.order_index) for item in result],
            [("c", 0), ("a", 10), ("b", 20)],
        )

    def test_player_payload_uses_playlist_item_order_and_repeat_count(self):
        first = _item("1", 0, repeat_count=2)
        inactive = _item("2", 10, is_active=False)
        third = _item("3", 20)
        media = [
            _media("media-3", "Terceira"),
            _media("media-1", "Primeira"),
            _media("media-2", "Inativa"),
        ]
        campaign = SimpleNamespace(id="campaign-1", audio_policy=None)
        db = FakeMediaSession(media)

        with patch(
            "api.v1.devices._resolve_playlist_entries",
            return_value=[
                (third, "media-3"),
                (inactive, "media-2"),
                (first, "media-1"),
            ],
        ):
            payload = _build_media_payload(db, campaign=campaign)

        self.assertEqual(
            [entry["media_id"] for entry in payload],
            ["media-3", "media-1", "media-1"],
        )
        self.assertEqual(
            [entry.get("item_id") for entry in payload],
            ["3", "1", "1"],
        )


if __name__ == "__main__":
    unittest.main()
