"""Testes SPEC 016 — arquivar/restaurar/excluir definitivamente de faixas de áudio.

Cobre: filtro de arquivadas por padrão em GET /audio/tracks, sincronização
de archived_at no enum status (PUT genérico e PATCH /status), e bloqueio de
exclusão definitiva quando a faixa está em uso (playlist/pasta/spot).
"""
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from api.v1.audio.tracks import (
    delete_audio_track,
    get_audio_tracks,
    update_audio_track,
)
from core.models import AudioTrack
from core.schemas_completos import AudioTrackUpdate
from crud.entidades.crud_audio_track import crud_audio_track


def _make_track(**overrides):
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Faixa Teste",
        file_url="/uploads/audio/tracks/teste.mp3",
        status="active",
        archived_at=None,
    )
    defaults.update(overrides)
    return AudioTrack(**defaults)


class TestAudioTrackListingFilters(unittest.TestCase):
    def test_get_audio_tracks_excludes_archived_by_default(self):
        admin = SimpleNamespace(role="admin", tenant_id=None)
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        get_audio_tracks(
            db=db,
            current_user=admin,
            skip=0,
            limit=100,
            search=None,
            category=None,
            category_id=None,
            status=None,
            tenant_id=None,
            include_archived=False,
        )

        filter_calls = [str(c.args[0]) for c in query.filter.call_args_list]
        compiled = [
            c.args[0].compile(compile_kwargs={"literal_binds": True})
            for c in query.filter.call_args_list
        ]
        self.assertTrue(
            any("status" in c and "archived" in str(comp))
            for c, comp in zip(filter_calls, compiled)
        )

    def test_get_audio_tracks_include_archived_skips_default_filter(self):
        admin = SimpleNamespace(role="admin", tenant_id=None)
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        get_audio_tracks(
            db=db,
            current_user=admin,
            skip=0,
            limit=100,
            search=None,
            category=None,
            category_id=None,
            status=None,
            tenant_id=None,
            include_archived=True,
        )

        # Sem filtro explícito de status e include_archived=True: nenhuma
        # chamada a query.filter deve mencionar 'archived'.
        filter_calls = [str(c) for c in query.filter.call_args_list]
        self.assertFalse(
            any("archived" in c for c in filter_calls),
            f"Não deveria filtrar archived quando include_archived=True: {filter_calls}",
        )

    def test_get_audio_tracks_explicit_status_overrides_default_filter(self):
        from core.schemas_completos import AudioTrackStatusEnum

        admin = SimpleNamespace(role="admin", tenant_id=None)
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        get_audio_tracks(
            db=db,
            current_user=admin,
            skip=0,
            limit=100,
            search=None,
            category=None,
            category_id=None,
            status=AudioTrackStatusEnum.ARCHIVED,
            tenant_id=None,
            include_archived=False,
        )

        # status=archived explícito deve ser respeitado mesmo com
        # include_archived=False (não aplica o filtro "exclude" duplicado).
        # admin + tenant_id=None -> filtro de tenant é pulado; só o de status roda.
        self.assertEqual(query.filter.call_count, 1)


class TestAudioTrackArchivedAtSync(unittest.TestCase):
    def test_archiving_via_put_sets_archived_at(self):
        track = _make_track(status="active", archived_at=None)
        user = SimpleNamespace(role="admin", tenant_id=track.tenant_id)
        db = MagicMock()

        with patch("api.v1.audio.tracks.crud_audio_track.get", return_value=track), \
             patch("api.v1.audio.tracks._notify_track_changed"):
            update_audio_track(
                db=db,
                current_user=user,
                track_id=str(track.id),
                track_in=AudioTrackUpdate(status="archived"),
            )

        self.assertEqual(track.status, "archived")
        self.assertIsNotNone(track.archived_at)

    def test_restoring_via_put_clears_archived_at(self):
        from datetime import datetime

        track = _make_track(status="archived", archived_at=datetime(2026, 6, 1))
        user = SimpleNamespace(role="admin", tenant_id=track.tenant_id)
        db = MagicMock()

        with patch("api.v1.audio.tracks.crud_audio_track.get", return_value=track), \
             patch("api.v1.audio.tracks._notify_track_changed"):
            update_audio_track(
                db=db,
                current_user=user,
                track_id=str(track.id),
                track_in=AudioTrackUpdate(status="active"),
            )

        self.assertEqual(track.status, "active")
        self.assertIsNone(track.archived_at)

    def test_update_without_status_field_does_not_touch_archived_at(self):
        from datetime import datetime

        sentinel = datetime(2026, 6, 1)
        track = _make_track(status="archived", archived_at=sentinel)
        user = SimpleNamespace(role="admin", tenant_id=track.tenant_id)
        db = MagicMock()

        with patch("api.v1.audio.tracks.crud_audio_track.get", return_value=track), \
             patch("api.v1.audio.tracks._notify_track_changed"):
            update_audio_track(
                db=db,
                current_user=user,
                track_id=str(track.id),
                track_in=AudioTrackUpdate(name="Novo nome"),
            )

        self.assertEqual(track.archived_at, sentinel)

    def test_update_status_helper_keeps_archived_at_in_sync(self):
        db = MagicMock()
        track = _make_track(status="active", archived_at=None)

        crud_audio_track.update_status(db, db_obj=track, status="archived")
        self.assertIsNotNone(track.archived_at)

        crud_audio_track.update_status(db, db_obj=track, status="active")
        self.assertIsNone(track.archived_at)


class TestAudioTrackHardDeleteGuard(unittest.TestCase):
    def test_delete_blocked_when_track_in_use(self):
        track = _make_track()
        user = SimpleNamespace(role="admin", tenant_id=track.tenant_id)
        db = MagicMock()

        with patch("api.v1.audio.tracks.crud_audio_track.get", return_value=track), \
             patch(
                 "api.v1.audio.tracks.crud_audio_track.get_in_use_references",
                 return_value={"playlists": 1, "folders": 0, "spots": 0, "in_use": True},
             ):
            with self.assertRaises(HTTPException) as ctx:
                delete_audio_track(db=db, current_user=user, track_id=str(track.id))

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("playlists", str(ctx.exception.detail))

    def test_delete_allowed_when_track_not_in_use(self):
        track = _make_track()
        user = SimpleNamespace(role="admin", tenant_id=track.tenant_id)
        db = MagicMock()

        with patch("api.v1.audio.tracks.crud_audio_track.get", return_value=track), \
             patch(
                 "api.v1.audio.tracks.crud_audio_track.get_in_use_references",
                 return_value={"playlists": 0, "folders": 0, "spots": 0, "in_use": False},
             ), \
             patch("api.v1.audio.tracks.crud_audio_track.remove") as remove_mock, \
             patch("api.v1.audio.tracks._notify_track_changed"), \
             patch("os.path.exists", return_value=False):
            result = delete_audio_track(db=db, current_user=user, track_id=str(track.id))

        remove_mock.assert_called_once()
        self.assertIn("removida", result["message"])


class TestAudioTrackInUseReferences(unittest.TestCase):
    def test_get_in_use_references_counts_all_sources(self):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.count.side_effect = [2, 0, 1]  # playlists, folders, spots

        refs = crud_audio_track.get_in_use_references(db, track_id="track-1")

        self.assertEqual(refs["playlists"], 2)
        self.assertEqual(refs["folders"], 0)
        self.assertEqual(refs["spots"], 1)
        self.assertTrue(refs["in_use"])

    def test_get_in_use_references_not_in_use_when_all_zero(self):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.count.side_effect = [0, 0, 0]

        refs = crud_audio_track.get_in_use_references(db, track_id="track-1")
        self.assertFalse(refs["in_use"])


if __name__ == "__main__":
    unittest.main()
