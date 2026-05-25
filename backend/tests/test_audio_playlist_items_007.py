import unittest
from datetime import datetime
from types import SimpleNamespace

from api.v1.devices import _audio_playlist_track_payload
from core.models import AudioPlaylistItem, AudioTrack
from crud.entidades.crud_audio_playlist_item import crud_audio_playlist_item


def _item(item_id, track_id, order_index, *, is_active=True, volume_override=None):
    return SimpleNamespace(
        id=item_id,
        playlist_id="playlist-1",
        track_id=track_id,
        order_index=order_index,
        created_at=datetime(2026, 5, 23, 9, order_index),
        is_active=is_active,
        volume_override=volume_override,
    )


def _track(track_id, name):
    return SimpleNamespace(
        id=track_id,
        name=name,
        file_url=f"/uploads/audio/{track_id}.mp3",
        duration_seconds=90,
        status="active",
    )


class FakeItemQuery:
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


class FakeTrackQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *_args, **_kwargs):
        return self

    def all(self):
        return self.rows


class FakeSession:
    def __init__(self, *, items=None, tracks=None):
        self.items = items or []
        self.tracks = tracks or []

    def query(self, model):
        if model is AudioPlaylistItem:
            return FakeItemQuery(self.items)
        if model is AudioTrack:
            return FakeTrackQuery(self.tracks)
        raise AssertionError(f"Unexpected query model: {model!r}")

    def add(self, _obj):
        return None

    def flush(self):
        return None


class AudioPlaylistItemsTest(unittest.TestCase):
    def test_apply_reorder_compacts_playlist_items(self):
        first = _item("item-a", "track-a", 0)
        second = _item("item-b", "track-b", 10)
        third = _item("item-c", "track-c", 20)
        db = FakeSession(items=[first, second, third])

        result = crud_audio_playlist_item.apply_reorder(
            db,
            playlist_id="playlist-1",
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

    def test_player_audio_payload_prefers_relational_items(self):
        items = [
            _item("item-a", "track-a", 20),
            _item("item-b", "track-b", 0, volume_override=0.35),
            _item("item-c", "track-c", 10, is_active=False),
        ]
        tracks = [
            _track("track-a", "A"),
            _track("track-b", "B"),
            _track("track-c", "C"),
        ]
        playlist = SimpleNamespace(
            id="playlist-1",
            track_ids=["track-c", "track-a"],
            track_volumes={"track-a": 0.9},
            volume_default=0.7,
        )

        payload = _audio_playlist_track_payload(
            FakeSession(items=items, tracks=tracks),
            playlist=playlist,
        )

        self.assertEqual([track["id"] for track in payload], ["track-b", "track-a"])
        self.assertEqual([track["volume"] for track in payload], [0.35, 0.9])

    def test_player_audio_payload_falls_back_to_legacy_track_ids(self):
        playlist = SimpleNamespace(
            id="playlist-1",
            track_ids=["track-b", "track-a"],
            track_volumes={"track-b": 0.5},
            volume_default=0.7,
        )

        payload = _audio_playlist_track_payload(
            FakeSession(
                items=[],
                tracks=[_track("track-a", "A"), _track("track-b", "B")],
            ),
            playlist=playlist,
        )

        self.assertEqual([track["id"] for track in payload], ["track-b", "track-a"])
        self.assertEqual([track["volume"] for track in payload], [0.5, 0.7])

    def test_player_audio_payload_does_not_fallback_when_items_are_inactive(self):
        playlist = SimpleNamespace(
            id="playlist-1",
            track_ids=["track-a"],
            track_volumes={},
            volume_default=0.7,
        )

        payload = _audio_playlist_track_payload(
            FakeSession(
                items=[_item("item-a", "track-a", 0, is_active=False)],
                tracks=[_track("track-a", "A")],
            ),
            playlist=playlist,
        )

        self.assertEqual(payload, [])


if __name__ == "__main__":
    unittest.main()
