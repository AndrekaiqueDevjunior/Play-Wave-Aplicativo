"""Testes RÁDIO INDOOR — Validação completa de todos os endpoints.

Módulos cobertos:
  - /audio/tracks    → Faixas de Áudio (12 endpoints)
  - /audio/playlists → Playlists Sonoras (23 endpoints)
  - /audio/folders   → Pastas de Áudio (11 endpoints)
  - /audio/spots     → Spots de Áudio (11 endpoints)

Padrões testados:
  - GET lista → 200
  - GET por ID → 200 / 403 cross-tenant / 404 not found
  - POST criar → 200 ou 201
  - PUT atualizar → 200 / 403 / 404
  - DELETE → 204 ou 200 / 403 / 404
  - PATCH status → 200 / 422 valor inválido
  - Sub-recursos (tracks em playlists, tracks em folders, schedules)
"""

import unittest
import uuid
from datetime import datetime, time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


# ── helpers ──────────────────────────────────────────────────────────────────

NULL_UUID = "00000000-0000-0000-0000-000000000000"


def _make_user(**kw):
    base = dict(
        id=uuid.uuid4(),
        email="admin@test.com",
        role="admin",
        tenant_id=uuid.uuid4(),
        is_active=True,
        name="Admin",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_track(**kw):
    tid = uuid.uuid4()
    base = dict(
        id=uuid.uuid4(),
        tenant_id=tid,
        name="Faixa Teste",
        artist=None,
        album=None,
        duration_seconds=180,
        file_url="/uploads/audio.mp3",
        file_size=1024,
        category="music",  # valid: music, jingle, announcement, ambient, other
        status="active",
        is_active=True,
        tags=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_playlist(**kw):
    tid = uuid.uuid4()
    base = dict(
        id=uuid.uuid4(),
        tenant_id=tid,
        name="Playlist Teste",
        description=None,
        status="active",
        is_active=True,
        volume=80,
        shuffle=False,
        repeat=True,
        folder_id=None,
        tags=[],
        items=[],
        track_ids=[],  # used in create_audio_playlist post-create logic
        total_duration_seconds=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_folder(**kw):
    tid = uuid.uuid4()
    base = dict(
        id=uuid.uuid4(),
        tenant_id=tid,
        name="Pasta Teste",
        description=None,
        status="active",
        is_active=True,
        color=None,
        icon=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_spot(**kw):
    tid = uuid.uuid4()
    base = dict(
        id=uuid.uuid4(),
        tenant_id=tid,
        name="Spot Teste",
        description=None,
        status="active",
        is_active=True,
        track_id=str(uuid.uuid4()),  # required field in AudioSpotResponse
        insertion_policy="wait_silence",
        tags=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_playlist_item(**kw):
    base = dict(
        id=uuid.uuid4(),
        playlist_id=uuid.uuid4(),
        track_id=uuid.uuid4(),
        order_index=10,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_folder_track(**kw):
    base = dict(
        id=uuid.uuid4(),
        folder_id=uuid.uuid4(),
        track_id=uuid.uuid4(),
        order_index=10,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_spot_schedule(**kw):
    base = dict(
        id=uuid.uuid4(),
        spot_id=uuid.uuid4(),
        weekdays=[1, 2, 3],
        start_time=time(8, 0),
        end_time=time(18, 0),
        interval_minutes=60,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _app_for(router_module, router_attr, user, fake_db=None):
    import importlib
    mod = importlib.import_module(router_module)
    router = getattr(mod, router_attr)

    from core.database import get_db
    from core.dependencies import get_current_user

    app = FastAPI()
    app.include_router(router)

    if fake_db is None:
        fake_db = MagicMock()
        fake_db.query.return_value.filter.return_value = fake_db.query.return_value
        fake_db.query.return_value.all.return_value = []
        fake_db.query.return_value.first.return_value = None
        fake_db.query.return_value.count.return_value = 0
        fake_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        fake_db.query.return_value.order_by.return_value.all.return_value = []
        fake_db.query.return_value.order_by.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


# ═══════════════════════════════════════════════════════════════════════
# FAIXAS DE ÁUDIO  /audio/tracks
# ═══════════════════════════════════════════════════════════════════════

class TestAudioTracksEndpoints(unittest.TestCase):
    def _client(self, user=None):
        return _app_for("api.v1.audio.tracks", "router", user or _make_user())

    # GET /
    def test_list_tracks_returns_200(self):
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.get_multi.return_value = []
            resp = self._client().get("/audio/tracks/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_list_tracks_with_search_returns_200(self):
        client = self._client()
        resp = client.get("/audio/tracks/?search=samba")
        self.assertEqual(resp.status_code, 200)

    def test_list_tracks_with_category_filter_returns_200(self):
        client = self._client()
        resp = client.get("/audio/tracks/?category=music")
        self.assertEqual(resp.status_code, 200)

    def test_list_tracks_with_status_filter_returns_200(self):
        client = self._client()
        resp = client.get("/audio/tracks/?status=active")
        self.assertEqual(resp.status_code, 200)

    # GET /statistics/overview
    def test_statistics_returns_200(self):
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.get_statistics.return_value = {"total": 0, "active": 0, "inactive": 0}
            resp = self._client().get("/audio/tracks/statistics/overview")
        self.assertEqual(resp.status_code, 200)

    # GET /active/list
    def test_active_list_returns_200(self):
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.get_active.return_value = []
            resp = self._client().get("/audio/tracks/active/list")
        self.assertEqual(resp.status_code, 200)

    # GET /by-category/{category}
    def test_by_category_returns_200(self):
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.get_by_category.return_value = []
            resp = self._client().get("/audio/tracks/by-category/music")
        self.assertEqual(resp.status_code, 200)

    # GET /by-duration
    def test_by_duration_returns_200(self):
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.get_by_duration_range.return_value = []
            resp = self._client().get("/audio/tracks/by-duration?min_seconds=30&max_seconds=300")
        self.assertEqual(resp.status_code, 200)

    # GET /{id}
    def test_get_track_by_id_returns_200(self):
        tid = uuid.uuid4()
        track = _make_track(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.get.return_value = track
            resp = _app_for("api.v1.audio.tracks", "router", user).get(f"/audio/tracks/{track.id}")
        self.assertEqual(resp.status_code, 200)

    def test_get_track_not_found_returns_404(self):
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.get.return_value = None
            resp = self._client().get(f"/audio/tracks/{NULL_UUID}")
        self.assertEqual(resp.status_code, 404)

    def test_get_track_cross_tenant_returns_403(self):
        track = _make_track(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.get.return_value = track
            resp = _app_for("api.v1.audio.tracks", "router", user).get(f"/audio/tracks/{track.id}")
        self.assertEqual(resp.status_code, 403)

    # POST /
    def test_create_track_returns_200_or_201(self):
        tid = uuid.uuid4()
        track = _make_track(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.create.return_value = track
            resp = _app_for("api.v1.audio.tracks", "router", user).post("/audio/tracks/", json={
                "name": "Nova Faixa",
                "file_url": "/uploads/audio.mp3",
                "tenant_id": str(tid),
            })
        self.assertIn(resp.status_code, (200, 201))

    def test_create_track_missing_name_returns_422(self):
        resp = self._client().post("/audio/tracks/", json={})
        self.assertEqual(resp.status_code, 422)

    # PUT /{id}
    def test_update_track_returns_200(self):
        tid = uuid.uuid4()
        track = _make_track(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.get.return_value = track
            m.update.return_value = track
            resp = _app_for("api.v1.audio.tracks", "router", user).put(
                f"/audio/tracks/{track.id}", json={"name": "Novo Nome"}
            )
        self.assertEqual(resp.status_code, 200)

    def test_update_track_not_found_returns_404(self):
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.get.return_value = None
            resp = self._client().put(f"/audio/tracks/{NULL_UUID}", json={"name": "X"})
        self.assertEqual(resp.status_code, 404)

    def test_update_track_cross_tenant_returns_403(self):
        track = _make_track(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.get.return_value = track
            resp = _app_for("api.v1.audio.tracks", "router", user).put(
                f"/audio/tracks/{track.id}", json={"name": "X"}
            )
        self.assertEqual(resp.status_code, 403)

    # DELETE /{id}
    def test_delete_track_not_found_returns_404(self):
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.get.return_value = None
            resp = self._client().delete(f"/audio/tracks/{NULL_UUID}")
        self.assertEqual(resp.status_code, 404)

    def test_delete_track_cross_tenant_returns_403(self):
        track = _make_track(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.get.return_value = track
            resp = _app_for("api.v1.audio.tracks", "router", user).delete(
                f"/audio/tracks/{track.id}"
            )
        self.assertEqual(resp.status_code, 403)

    # PATCH /{id}/status
    def test_patch_status_returns_200(self):
        tid = uuid.uuid4()
        track = _make_track(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.tracks.crud_audio_track") as m:
            m.get.return_value = track
            m.update_status.return_value = track
            resp = _app_for("api.v1.audio.tracks", "router", user).patch(
                f"/audio/tracks/{track.id}/status?status=inactive"
            )
        self.assertEqual(resp.status_code, 200)

    def test_patch_status_invalid_returns_422(self):
        resp = self._client().patch(f"/audio/tracks/{NULL_UUID}/status?status=nao_existe")
        self.assertEqual(resp.status_code, 422)


# ═══════════════════════════════════════════════════════════════════════
# PLAYLISTS SONORAS  /audio/playlists
# ═══════════════════════════════════════════════════════════════════════

class TestAudioPlaylistsEndpoints(unittest.TestCase):
    def _client(self, user=None):
        return _app_for("api.v1.audio.playlists", "router", user or _make_user())

    # GET /
    def test_list_playlists_returns_200(self):
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m:
            m.get_multi.return_value = []
            resp = self._client().get("/audio/playlists/")
        self.assertEqual(resp.status_code, 200)

    def test_list_with_search_returns_200(self):
        client = self._client()
        resp = client.get("/audio/playlists/?search=natal")
        self.assertEqual(resp.status_code, 200)

    def test_list_with_status_filter_returns_200(self):
        client = self._client()
        resp = client.get("/audio/playlists/?status=active")
        self.assertEqual(resp.status_code, 200)

    # GET /statistics/overview
    def test_statistics_returns_200(self):
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m:
            m.get_statistics.return_value = {"total": 0, "active": 0}
            resp = self._client().get("/audio/playlists/statistics/overview")
        self.assertEqual(resp.status_code, 200)

    # GET /active/list
    def test_active_list_returns_200(self):
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m:
            m.get_active.return_value = []
            resp = self._client().get("/audio/playlists/active/list")
        self.assertEqual(resp.status_code, 200)

    # GET /{id}
    def test_get_playlist_by_id_returns_200(self):
        tid = uuid.uuid4()
        pl = _make_playlist(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m:
            m.get.return_value = pl
            resp = _app_for("api.v1.audio.playlists", "router", user).get(
                f"/audio/playlists/{pl.id}"
            )
        self.assertEqual(resp.status_code, 200)

    def test_get_playlist_not_found_returns_404(self):
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m:
            m.get.return_value = None
            resp = self._client().get(f"/audio/playlists/{NULL_UUID}")
        self.assertEqual(resp.status_code, 404)

    def test_get_playlist_cross_tenant_returns_403(self):
        pl = _make_playlist(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m:
            m.get.return_value = pl
            resp = _app_for("api.v1.audio.playlists", "router", user).get(
                f"/audio/playlists/{pl.id}"
            )
        self.assertEqual(resp.status_code, 403)

    # GET /{id}/with-tracks
    def test_get_playlist_with_tracks_returns_200(self):
        tid = uuid.uuid4()
        pl = _make_playlist(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m:
            m.get.return_value = pl
            m.get_with_tracks.return_value = pl
            resp = _app_for("api.v1.audio.playlists", "router", user).get(
                f"/audio/playlists/{pl.id}/with-tracks"
            )
        self.assertEqual(resp.status_code, 200)

    # GET /{id}/items
    def test_get_playlist_items_returns_200(self):
        tid = uuid.uuid4()
        pl = _make_playlist(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m, \
             patch("api.v1.audio.playlists.crud_audio_playlist_item") as mi:
            m.get.return_value = pl
            mi.list_by_playlist.return_value = []
            resp = _app_for("api.v1.audio.playlists", "router", user).get(
                f"/audio/playlists/{pl.id}/items"
            )
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    # POST /
    def test_create_playlist_returns_200_or_201(self):
        tid = uuid.uuid4()
        pl = _make_playlist(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m:
            m.create.return_value = pl
            resp = _app_for("api.v1.audio.playlists", "router", user).post(
                "/audio/playlists/", json={"name": "Nova Playlist", "tenant_id": str(tid)}
            )
        self.assertIn(resp.status_code, (200, 201))

    def test_create_playlist_missing_name_returns_422(self):
        resp = self._client().post("/audio/playlists/", json={})
        self.assertEqual(resp.status_code, 422)

    # PUT /{id}
    def test_update_playlist_returns_200(self):
        tid = uuid.uuid4()
        pl = _make_playlist(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m, \
             patch("api.v1.audio.playlists._invalidate_device_playlist_cache"):
            m.get.return_value = pl
            m.update.return_value = pl
            resp = _app_for("api.v1.audio.playlists", "router", user).put(
                f"/audio/playlists/{pl.id}", json={"name": "Novo Nome"}
            )
        self.assertEqual(resp.status_code, 200)

    def test_update_playlist_not_found_returns_404(self):
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m:
            m.get.return_value = None
            resp = self._client().put(f"/audio/playlists/{NULL_UUID}", json={"name": "X"})
        self.assertEqual(resp.status_code, 404)

    # DELETE /{id}
    def test_delete_playlist_not_found_returns_404(self):
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m:
            m.get.return_value = None
            resp = self._client().delete(f"/audio/playlists/{NULL_UUID}")
        self.assertEqual(resp.status_code, 404)

    def test_delete_playlist_cross_tenant_returns_403(self):
        pl = _make_playlist(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m:
            m.get.return_value = pl
            resp = _app_for("api.v1.audio.playlists", "router", user).delete(
                f"/audio/playlists/{pl.id}"
            )
        self.assertEqual(resp.status_code, 403)

    # PATCH /{id}/status
    def test_patch_status_returns_200(self):
        tid = uuid.uuid4()
        pl = _make_playlist(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m, \
             patch("api.v1.audio.playlists._invalidate_device_playlist_cache"):
            m.get.return_value = pl
            m.update_status.return_value = pl
            resp = _app_for("api.v1.audio.playlists", "router", user).patch(
                f"/audio/playlists/{pl.id}/status?status=inactive"
            )
        self.assertEqual(resp.status_code, 200)

    def test_patch_status_invalid_returns_422(self):
        resp = self._client().patch(f"/audio/playlists/{NULL_UUID}/status?status=nao_existe")
        self.assertEqual(resp.status_code, 422)

    # POST /{id}/tracks/{track_id} — adicionar faixa
    def test_add_track_to_playlist_not_found_playlist_returns_404(self):
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m:
            m.get.return_value = None
            resp = self._client().post(f"/audio/playlists/{NULL_UUID}/tracks/{NULL_UUID}")
        self.assertEqual(resp.status_code, 404)

    # DELETE /{id}/tracks/{track_id}
    def test_remove_track_from_playlist_not_found_playlist_returns_404(self):
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m:
            m.get.return_value = None
            resp = self._client().delete(f"/audio/playlists/{NULL_UUID}/tracks/{NULL_UUID}")
        self.assertEqual(resp.status_code, 404)

    # GET /by-device/{device_id}
    def test_by_device_not_found_returns_404(self):
        with patch("api.v1.audio.playlists.crud_audio_playlist") as m:
            m.get_by_device.return_value = None
            resp = self._client().get(f"/audio/playlists/by-device/{NULL_UUID}")
        self.assertEqual(resp.status_code, 404)


# ═══════════════════════════════════════════════════════════════════════
# PASTAS DE ÁUDIO  /audio/folders
# ═══════════════════════════════════════════════════════════════════════

class TestAudioFoldersEndpoints(unittest.TestCase):
    def _client(self, user=None):
        return _app_for("api.v1.audio.folders", "router", user or _make_user())

    def test_list_folders_returns_200(self):
        with patch("api.v1.audio.folders.crud_audio_folder") as m:
            m.get_multi.return_value = []
            resp = self._client().get("/audio/folders/")
        self.assertEqual(resp.status_code, 200)

    def test_active_list_returns_200(self):
        with patch("api.v1.audio.folders.crud_audio_folder") as m:
            m.get_active.return_value = []
            resp = self._client().get("/audio/folders/active/list")
        self.assertEqual(resp.status_code, 200)

    def test_get_folder_not_found_returns_404(self):
        with patch("api.v1.audio.folders.crud_audio_folder") as m:
            m.get.return_value = None
            resp = self._client().get(f"/audio/folders/{NULL_UUID}")
        self.assertEqual(resp.status_code, 404)

    def test_get_folder_cross_tenant_returns_403(self):
        folder = _make_folder(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        with patch("api.v1.audio.folders.crud_audio_folder") as m:
            m.get.return_value = folder
            resp = _app_for("api.v1.audio.folders", "router", user).get(
                f"/audio/folders/{folder.id}"
            )
        self.assertEqual(resp.status_code, 403)

    def test_get_folder_returns_200(self):
        tid = uuid.uuid4()
        folder = _make_folder(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.folders.crud_audio_folder") as m:
            m.get.return_value = folder
            resp = _app_for("api.v1.audio.folders", "router", user).get(
                f"/audio/folders/{folder.id}"
            )
        self.assertEqual(resp.status_code, 200)

    def test_create_folder_returns_200_or_201(self):
        tid = uuid.uuid4()
        folder = _make_folder(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.folders.crud_audio_folder") as m:
            m.create.return_value = folder
            resp = _app_for("api.v1.audio.folders", "router", user).post(
                "/audio/folders/", json={"name": "Nova Pasta", "tenant_id": str(tid)}
            )
        self.assertIn(resp.status_code, (200, 201))

    def test_create_folder_missing_name_returns_422(self):
        resp = self._client().post("/audio/folders/", json={})
        self.assertEqual(resp.status_code, 422)

    def test_update_folder_not_found_returns_404(self):
        with patch("api.v1.audio.folders.crud_audio_folder") as m:
            m.get.return_value = None
            resp = self._client().put(f"/audio/folders/{NULL_UUID}", json={"name": "X"})
        self.assertEqual(resp.status_code, 404)

    def test_update_folder_cross_tenant_returns_403(self):
        folder = _make_folder(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        with patch("api.v1.audio.folders.crud_audio_folder") as m:
            m.get.return_value = folder
            resp = _app_for("api.v1.audio.folders", "router", user).put(
                f"/audio/folders/{folder.id}", json={"name": "X"}
            )
        self.assertEqual(resp.status_code, 403)

    def test_delete_folder_not_found_returns_404(self):
        with patch("api.v1.audio.folders.crud_audio_folder") as m:
            m.get.return_value = None
            resp = self._client().delete(f"/audio/folders/{NULL_UUID}")
        self.assertEqual(resp.status_code, 404)

    # GET /{id}/tracks
    def test_folder_tracks_not_found_returns_404(self):
        with patch("api.v1.audio.folders.crud_audio_folder") as m:
            m.get.return_value = None
            resp = self._client().get(f"/audio/folders/{NULL_UUID}/tracks")
        self.assertEqual(resp.status_code, 404)

    def test_folder_tracks_returns_200(self):
        tid = uuid.uuid4()
        folder = _make_folder(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.folders.crud_audio_folder") as m, \
             patch("api.v1.audio.folders.crud_audio_folder_track") as mt:
            m.get.return_value = folder
            mt.list_by_folder.return_value = []
            resp = _app_for("api.v1.audio.folders", "router", user).get(
                f"/audio/folders/{folder.id}/tracks"
            )
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)


# ═══════════════════════════════════════════════════════════════════════
# SPOTS DE ÁUDIO  /audio/spots
# ═══════════════════════════════════════════════════════════════════════

class TestAudioSpotsEndpoints(unittest.TestCase):
    def _client(self, user=None):
        return _app_for("api.v1.audio.spots", "router", user or _make_user())

    def test_list_spots_returns_200(self):
        client = self._client()
        fake_db = MagicMock()
        fake_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = []
        fake_db.query.return_value.filter.return_value.count.return_value = 0
        with patch("api.v1.audio.spots.crud_audio_spot") as m:
            m.get_multi_filtered.return_value = ([], 0)
            resp = self._client().get("/audio/spots/")
        self.assertEqual(resp.status_code, 200)

    def test_get_spot_not_found_returns_404(self):
        with patch("api.v1.audio.spots.crud_audio_spot") as m:
            m.get.return_value = None
            resp = self._client().get(f"/audio/spots/{NULL_UUID}")
        self.assertEqual(resp.status_code, 404)

    def test_get_spot_cross_tenant_returns_403(self):
        spot = _make_spot(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        with patch("api.v1.audio.spots.crud_audio_spot") as m:
            m.get.return_value = spot
            resp = _app_for("api.v1.audio.spots", "router", user).get(
                f"/audio/spots/{spot.id}"
            )
        self.assertEqual(resp.status_code, 403)

    def test_get_spot_returns_200(self):
        tid = uuid.uuid4()
        spot = _make_spot(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.spots.crud_audio_spot") as m:
            m.get.return_value = spot
            resp = _app_for("api.v1.audio.spots", "router", user).get(
                f"/audio/spots/{spot.id}"
            )
        self.assertEqual(resp.status_code, 200)

    def test_create_spot_returns_201(self):
        tid = uuid.uuid4()
        track_id = str(uuid.uuid4())
        spot = _make_spot(tenant_id=tid, track_id=track_id)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.spots.crud_audio_spot") as m, \
             patch("api.v1.audio.spots._ensure_track_in_spot_scope") as mt:
            mt.return_value = SimpleNamespace(id=track_id, tenant_id=tid)
            m.create.return_value = spot
            resp = _app_for("api.v1.audio.spots", "router", user).post(
                "/audio/spots/",
                json={"name": "Novo Spot", "tenant_id": str(tid), "track_id": track_id},
            )
        self.assertIn(resp.status_code, (200, 201))

    def test_create_spot_missing_name_returns_422(self):
        resp = self._client().post("/audio/spots/", json={})
        self.assertEqual(resp.status_code, 422)

    def test_update_spot_not_found_returns_404(self):
        with patch("api.v1.audio.spots.crud_audio_spot") as m:
            m.get.return_value = None
            resp = self._client().put(f"/audio/spots/{NULL_UUID}", json={"name": "X"})
        self.assertEqual(resp.status_code, 404)

    def test_delete_spot_not_found_returns_204_or_404(self):
        with patch("api.v1.audio.spots.crud_audio_spot") as m:
            m.get.return_value = None
            resp = self._client().delete(f"/audio/spots/{NULL_UUID}")
        self.assertIn(resp.status_code, (204, 404))

    def test_delete_spot_cross_tenant_returns_403(self):
        spot = _make_spot(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        with patch("api.v1.audio.spots.crud_audio_spot") as m:
            m.get.return_value = spot
            resp = _app_for("api.v1.audio.spots", "router", user).delete(
                f"/audio/spots/{spot.id}"
            )
        self.assertEqual(resp.status_code, 403)

    # GET /playlists/{playlist_id}/spot-schedules (schedules are tied to playlists, not spots)
    def test_schedules_not_found_playlist_returns_404(self):
        with patch("api.v1.audio.spots.crud_audio_playlist") as m:
            m.get.return_value = None
            resp = self._client().get(
                f"/audio/spots/playlists/{NULL_UUID}/spot-schedules"
            )
        self.assertEqual(resp.status_code, 404)

    def test_schedules_returns_200(self):
        tid = uuid.uuid4()
        pl = _make_playlist(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        with patch("api.v1.audio.spots.crud_audio_playlist") as mp, \
             patch("api.v1.audio.spots.crud_audio_spot_schedule") as ms:
            mp.get.return_value = pl
            ms.get_by_playlist.return_value = []
            resp = _app_for("api.v1.audio.spots", "router", user).get(
                f"/audio/spots/playlists/{pl.id}/spot-schedules"
            )
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    # POST /playlists/{playlist_id}/spot-schedules
    def test_create_schedule_not_found_playlist_returns_404(self):
        with patch("api.v1.audio.spots.crud_audio_playlist") as m:
            m.get.return_value = None
            resp = self._client().post(
                f"/audio/spots/playlists/{NULL_UUID}/spot-schedules",
                json={"spot_id": str(uuid.uuid4()), "weekdays": [1],
                      "start_time": "08:00", "end_time": "18:00", "interval_seconds": 3600},
            )
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
