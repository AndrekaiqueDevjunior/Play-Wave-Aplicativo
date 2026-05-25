import unittest
from datetime import datetime
from types import SimpleNamespace

from pydantic import ValidationError

from core.models import AudioFolderTrack
from core.schemas_completos import AudioFolderCreate
from crud.entidades.crud_audio_folder_track import crud_audio_folder_track


def _folder_track(item_id, track_id, order_index):
    return SimpleNamespace(
        id=item_id,
        folder_id="folder-1",
        track_id=track_id,
        order_index=order_index,
        created_at=datetime(2026, 5, 23, 10, order_index),
        volume_override=None,
        is_active=True,
    )


class FakeFolderTrackQuery:
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
        return ordered[0] if ordered else None


class FakeFolderTrackSession:
    def __init__(self, rows):
        self.rows = rows

    def query(self, model):
        if model is not AudioFolderTrack:
            raise AssertionError(f"Unexpected query model: {model!r}")
        return FakeFolderTrackQuery(self.rows)

    def add(self, _obj):
        return None

    def flush(self):
        return None


class AudioFoldersTest(unittest.TestCase):
    def test_folder_period_rejects_end_before_start(self):
        with self.assertRaises(ValidationError):
            AudioFolderCreate(
                name="Manha",
                starts_at="2026-05-24T10:00:00",
                ends_at="2026-05-23T10:00:00",
            )

    def test_apply_reorder_compacts_folder_tracks(self):
        first = _folder_track("item-a", "track-a", 0)
        second = _folder_track("item-b", "track-b", 10)
        third = _folder_track("item-c", "track-c", 20)
        db = FakeFolderTrackSession([first, second, third])

        result = crud_audio_folder_track.apply_reorder(
            db,
            folder_id="folder-1",
            entries=[
                {"item_id": "item-c", "order_index": 0},
                {"item_id": "item-a", "order_index": 10},
                {"item_id": "item-b", "order_index": 20},
            ],
        )

        self.assertEqual([item.id for item in result], ["item-c", "item-a", "item-b"])
        self.assertEqual(
            [(item.id, item.order_index) for item in result],
            [("item-c", 0), ("item-a", 10), ("item-b", 20)],
        )


if __name__ == "__main__":
    unittest.main()
