"""Testes SPEC 017 — arquivar/restaurar/excluir definitivamente de playlists
sonoras.

Mesmo padrão da SPEC 016 (test_audio_track_archive_delete.py), adaptado para
AudioPlaylist: filtro de arquivadas por padrão em GET /audio/playlists,
sincronização de archived_at no enum status, e bloqueio de exclusão
definitiva quando a playlist está vinculada a um device ou campanha
(referência direta por FK, diferente das faixas que são referenciadas via
tabelas de junção).
"""
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from api.v1.audio.playlists import (
    delete_audio_playlist,
    get_audio_playlists,
    update_audio_playlist,
)
from core.models import AudioPlaylist
from core.schemas_completos import AudioPlaylistUpdate
from crud.entidades.crud_audio_playlist import crud_audio_playlist


def _make_playlist(**overrides):
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Playlist Teste",
        status="active",
        archived_at=None,
    )
    defaults.update(overrides)
    return AudioPlaylist(**defaults)


class TestAudioPlaylistListingFilters(unittest.TestCase):
    def test_get_audio_playlists_excludes_archived_by_default(self):
        admin = SimpleNamespace(role="admin", tenant_id=None)
        db = MagicMock()
        active_pl = _make_playlist(status="active")
        archived_pl = _make_playlist(status="archived", archived_at=None)

        with patch(
            "api.v1.audio.playlists.crud_audio_playlist.get_multi",
            return_value=[active_pl, archived_pl],
        ):
            result = get_audio_playlists(
                db=db,
                current_user=admin,
                skip=0,
                limit=100,
                search=None,
                status=None,
                category_id=None,
                tenant_id=None,
                include_archived=False,
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, active_pl.id)

    def test_get_audio_playlists_include_archived_keeps_archived(self):
        admin = SimpleNamespace(role="admin", tenant_id=None)
        db = MagicMock()
        active_pl = _make_playlist(status="active")
        archived_pl = _make_playlist(status="archived")

        with patch(
            "api.v1.audio.playlists.crud_audio_playlist.get_multi",
            return_value=[active_pl, archived_pl],
        ):
            result = get_audio_playlists(
                db=db,
                current_user=admin,
                skip=0,
                limit=100,
                search=None,
                status=None,
                category_id=None,
                tenant_id=None,
                include_archived=True,
            )

        self.assertEqual(len(result), 2)

    def test_get_audio_playlists_explicit_status_overrides_default_filter(self):
        from core.schemas_completos import AudioPlaylistStatusEnum

        admin = SimpleNamespace(role="admin", tenant_id=None)
        db = MagicMock()
        archived_pl = _make_playlist(status="archived")

        with patch(
            "api.v1.audio.playlists.crud_audio_playlist.get_by_status",
            return_value=[archived_pl],
        ):
            result = get_audio_playlists(
                db=db,
                current_user=admin,
                skip=0,
                limit=100,
                search=None,
                status=AudioPlaylistStatusEnum.ARCHIVED,
                category_id=None,
                tenant_id=None,
                include_archived=False,
            )

        # status=archived explícito deve trazer a arquivada mesmo com
        # include_archived=False.
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, archived_pl.id)


class TestAudioPlaylistArchivedAtSync(unittest.TestCase):
    def test_archiving_via_put_sets_archived_at(self):
        playlist = _make_playlist(status="active", archived_at=None)
        user = SimpleNamespace(role="admin", tenant_id=playlist.tenant_id)
        db = MagicMock()

        with patch("api.v1.audio.playlists.crud_audio_playlist.get", return_value=playlist), \
             patch("api.v1.audio.playlists._device_ids_for_playlist", return_value=set()), \
             patch("api.v1.audio.playlists._invalidate_device_playlist_cache"), \
             patch("api.v1.audio.playlists._publish_playlist_invalidated"):
            update_audio_playlist(
                db=db,
                current_user=user,
                playlist_id=str(playlist.id),
                playlist_in=AudioPlaylistUpdate(status="archived"),
            )

        self.assertEqual(playlist.status, "archived")
        self.assertIsNotNone(playlist.archived_at)

    def test_restoring_via_put_clears_archived_at(self):
        from datetime import datetime

        playlist = _make_playlist(status="archived", archived_at=datetime(2026, 6, 1))
        user = SimpleNamespace(role="admin", tenant_id=playlist.tenant_id)
        db = MagicMock()

        with patch("api.v1.audio.playlists.crud_audio_playlist.get", return_value=playlist), \
             patch("api.v1.audio.playlists._device_ids_for_playlist", return_value=set()), \
             patch("api.v1.audio.playlists._invalidate_device_playlist_cache"), \
             patch("api.v1.audio.playlists._publish_playlist_invalidated"):
            update_audio_playlist(
                db=db,
                current_user=user,
                playlist_id=str(playlist.id),
                playlist_in=AudioPlaylistUpdate(status="active"),
            )

        self.assertEqual(playlist.status, "active")
        self.assertIsNone(playlist.archived_at)

    def test_update_status_helper_keeps_archived_at_in_sync(self):
        db = MagicMock()
        playlist = _make_playlist(status="active", archived_at=None)

        crud_audio_playlist.update_status(db, db_obj=playlist, status="archived")
        self.assertIsNotNone(playlist.archived_at)

        crud_audio_playlist.update_status(db, db_obj=playlist, status="active")
        self.assertIsNone(playlist.archived_at)


class TestAudioPlaylistHardDeleteGuard(unittest.TestCase):
    def test_delete_blocked_when_linked_to_device(self):
        playlist = _make_playlist()
        user = SimpleNamespace(role="admin", tenant_id=playlist.tenant_id)
        db = MagicMock()

        with patch("api.v1.audio.playlists.crud_audio_playlist.get", return_value=playlist), \
             patch(
                 "api.v1.audio.playlists.crud_audio_playlist.get_in_use_references",
                 return_value={"devices": 2, "campaigns": 0, "in_use": True},
             ):
            with self.assertRaises(HTTPException) as ctx:
                delete_audio_playlist(db=db, current_user=user, playlist_id=str(playlist.id))

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("dispositivos", str(ctx.exception.detail))

    def test_delete_blocked_when_linked_to_campaign(self):
        playlist = _make_playlist()
        user = SimpleNamespace(role="admin", tenant_id=playlist.tenant_id)
        db = MagicMock()

        with patch("api.v1.audio.playlists.crud_audio_playlist.get", return_value=playlist), \
             patch(
                 "api.v1.audio.playlists.crud_audio_playlist.get_in_use_references",
                 return_value={"devices": 0, "campaigns": 1, "in_use": True},
             ):
            with self.assertRaises(HTTPException) as ctx:
                delete_audio_playlist(db=db, current_user=user, playlist_id=str(playlist.id))

        self.assertEqual(ctx.exception.status_code, 409)

    def test_delete_allowed_when_not_linked(self):
        playlist = _make_playlist()
        user = SimpleNamespace(role="admin", tenant_id=playlist.tenant_id)
        db = MagicMock()

        with patch("api.v1.audio.playlists.crud_audio_playlist.get", return_value=playlist), \
             patch(
                 "api.v1.audio.playlists.crud_audio_playlist.get_in_use_references",
                 return_value={"devices": 0, "campaigns": 0, "in_use": False},
             ), \
             patch("api.v1.audio.playlists._device_ids_for_playlist", return_value=set()), \
             patch("api.v1.audio.playlists.crud_audio_playlist.remove") as remove_mock, \
             patch("api.v1.audio.playlists._invalidate_device_playlist_cache"), \
             patch("api.v1.audio.playlists._publish_playlist_invalidated"):
            result = delete_audio_playlist(db=db, current_user=user, playlist_id=str(playlist.id))

        remove_mock.assert_called_once()
        self.assertIn("removida", result["message"])


class TestAudioPlaylistInUseReferences(unittest.TestCase):
    def test_get_in_use_references_counts_devices_and_campaigns(self):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.count.side_effect = [3, 1]  # devices, campaigns

        refs = crud_audio_playlist.get_in_use_references(db, playlist_id="playlist-1")

        self.assertEqual(refs["devices"], 3)
        self.assertEqual(refs["campaigns"], 1)
        self.assertTrue(refs["in_use"])

    def test_get_in_use_references_not_in_use_when_all_zero(self):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.count.side_effect = [0, 0]

        refs = crud_audio_playlist.get_in_use_references(db, playlist_id="playlist-1")
        self.assertFalse(refs["in_use"])


if __name__ == "__main__":
    unittest.main()
