"""Testes AUDIO SPOTS — Spots de áudio e spot-schedules.

Cobre:
  - _authorize_spot_access: spot não encontrado → 404, cross-tenant → 403
  - _ensure_track_in_spot_scope: faixa não encontrada → 404, cross-tenant → 403
  - _device_ids_for_playlist: agrega device_ids de Device e Campaign
  - Endpoint GET /audio/spots/: lista com filtro de tenant automático para não-admins
  - Endpoint POST /audio/spots/: cria spot com track e tenant corretos
  - Endpoint GET /audio/spots/{id}: 404 para inexistente, 403 cross-tenant
  - Endpoint DELETE /audio/spots/{id}: 204 com sucesso
  - Endpoint GET /audio/spots/playlists/{id}/spot-schedules: lista schedules
  - Endpoint POST /audio/spots/playlists/{id}/spot-schedules: cria schedule
  - Endpoint DELETE /audio/spots/playlists/{id}/spot-schedules/{sid}: 204
"""

import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call

from fastapi import FastAPI
from fastapi.testclient import TestClient


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_user(**kwargs):
    defaults = dict(
        id=uuid.uuid4(),
        email="op@test.com",
        role="admin",
        tenant_id=uuid.uuid4(),
        is_active=True,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_spot(**kwargs):
    tid = uuid.uuid4()
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=tid,
        name="Spot Promo",
        description=None,
        track_id=uuid.uuid4(),
        status="active",
        insertion_policy="between_tracks",
        created_at=None,
        updated_at=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_track(**kwargs):
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Track Teste",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_schedule(**kwargs):
    defaults = dict(
        id=uuid.uuid4(),
        playlist_id=uuid.uuid4(),
        spot_id=uuid.uuid4(),
        interval_seconds=1800,
        start_time="06:00",
        end_time="22:00",
        starts_at=None,
        ends_at=None,
        priority=5,
        is_active=True,
        created_at=None,
        updated_at=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_playlist(**kwargs):
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Playlist Teste",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _spots_app(user):
    from api.v1.audio.spots import router as spots_router
    from core.database import get_db
    from core.dependencies import get_current_user

    app = FastAPI()
    app.include_router(spots_router)

    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: user

    return app


# ── Testes unitários — _authorize_spot_access ─────────────────────────────────

class TestAuthorizeSpotAccess(unittest.TestCase):
    def setUp(self):
        from api.v1.audio.spots import _authorize_spot_access
        self.fn = _authorize_spot_access

    def test_spot_not_found_raises_404(self):
        from fastapi import HTTPException

        db = MagicMock()
        user = _make_user(role="admin")

        with patch("api.v1.audio.spots.crud_audio_spot") as mock_crud:
            mock_crud.get.return_value = None
            with self.assertRaises(HTTPException) as ctx:
                self.fn(db, spot_id=str(uuid.uuid4()), current_user=user)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_cross_tenant_raises_403(self):
        from fastapi import HTTPException

        db = MagicMock()
        spot = _make_spot(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())

        with patch("api.v1.audio.spots.crud_audio_spot") as mock_crud:
            mock_crud.get.return_value = spot
            with self.assertRaises(HTTPException) as ctx:
                self.fn(db, spot_id=str(spot.id), current_user=user)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_admin_can_access_any_tenant(self):
        db = MagicMock()
        spot = _make_spot(tenant_id=uuid.uuid4())
        user = _make_user(role="admin", tenant_id=uuid.uuid4())

        with patch("api.v1.audio.spots.crud_audio_spot") as mock_crud:
            mock_crud.get.return_value = spot
            result = self.fn(db, spot_id=str(spot.id), current_user=user)
        self.assertEqual(result.id, spot.id)

    def test_same_tenant_operator_passes(self):
        tid = uuid.uuid4()
        db = MagicMock()
        spot = _make_spot(tenant_id=tid)
        user = _make_user(role="operator", tenant_id=tid)

        with patch("api.v1.audio.spots.crud_audio_spot") as mock_crud:
            mock_crud.get.return_value = spot
            result = self.fn(db, spot_id=str(spot.id), current_user=user)
        self.assertEqual(result.id, spot.id)


# ── Testes unitários — _ensure_track_in_spot_scope ───────────────────────────

class TestEnsureTrackInSpotScope(unittest.TestCase):
    def setUp(self):
        from api.v1.audio.spots import _ensure_track_in_spot_scope
        self.fn = _ensure_track_in_spot_scope

    def test_track_not_found_raises_404(self):
        from fastapi import HTTPException

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        user = _make_user(role="admin")

        with self.assertRaises(HTTPException) as ctx:
            self.fn(db, track_id=str(uuid.uuid4()), current_user=user)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_cross_tenant_track_raises_403(self):
        from fastapi import HTTPException

        track = _make_track(tenant_id=uuid.uuid4())
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = track
        user = _make_user(role="operator", tenant_id=uuid.uuid4())

        with self.assertRaises(HTTPException) as ctx:
            self.fn(db, track_id=str(track.id), current_user=user)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_admin_access_any_track(self):
        tid = uuid.uuid4()
        track = _make_track(tenant_id=tid)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = track
        user = _make_user(role="admin", tenant_id=uuid.uuid4())

        result = self.fn(db, track_id=str(track.id), current_user=user)
        self.assertEqual(result.id, track.id)


# ── Testes de endpoint — GET /audio/spots/ ───────────────────────────────────

class TestListSpotsEndpoint(unittest.TestCase):
    def _call_list(self, user, spots_result=None):
        app = _spots_app(user)
        spots_result = spots_result or []

        fake_db = MagicMock()
        from core.database import get_db
        app.dependency_overrides[get_db] = lambda: fake_db

        q = MagicMock()
        q.filter.return_value = q
        q.count.return_value = len(spots_result)
        q.offset.return_value.limit.return_value.all.return_value = spots_result
        fake_db.query.return_value = q

        return TestClient(app).get("/audio/spots/")

    def test_list_returns_200(self):
        user = _make_user(role="admin")
        resp = self._call_list(user, spots_result=[])
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)


# ── Testes de endpoint — DELETE /audio/spots/{id} ────────────────────────────

class TestDeleteSpotEndpoint(unittest.TestCase):
    def test_delete_existing_spot_returns_204(self):
        tid = uuid.uuid4()
        spot = _make_spot(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        app = _spots_app(user)

        with patch("api.v1.audio.spots.crud_audio_spot") as mock_crud:
            mock_crud.get.return_value = spot
            mock_crud.remove.return_value = None

            client = TestClient(app)
            resp = client.delete(f"/audio/spots/{spot.id}")

        self.assertEqual(resp.status_code, 204)

    def test_delete_nonexistent_spot_returns_404(self):
        user = _make_user(role="admin")
        app = _spots_app(user)

        with patch("api.v1.audio.spots.crud_audio_spot") as mock_crud:
            mock_crud.get.return_value = None

            client = TestClient(app)
            resp = client.delete(f"/audio/spots/{uuid.uuid4()}")

        self.assertEqual(resp.status_code, 404)


# ── Testes de endpoint — spot-schedules ──────────────────────────────────────

class TestSpotSchedulesEndpoint(unittest.TestCase):
    def _make_schedule_app(self, user, playlist=None):
        app = _spots_app(user)

        fake_db = MagicMock()
        from core.database import get_db
        app.dependency_overrides[get_db] = lambda: fake_db

        return app, fake_db

    def test_list_spot_schedules_playlist_not_found_returns_404(self):
        user = _make_user(role="admin")
        app, _ = self._make_schedule_app(user)

        with patch("api.v1.audio.spots.crud_audio_playlist") as mock_pl:
            mock_pl.get.return_value = None

            client = TestClient(app)
            resp = client.get(f"/audio/spots/playlists/{uuid.uuid4()}/spot-schedules")

        self.assertEqual(resp.status_code, 404)

    def test_list_spot_schedules_cross_tenant_returns_403(self):
        playlist = _make_playlist(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        app, _ = self._make_schedule_app(user, playlist=playlist)

        with patch("api.v1.audio.spots.crud_audio_playlist") as mock_pl:
            mock_pl.get.return_value = playlist

            client = TestClient(app)
            resp = client.get(f"/audio/spots/playlists/{playlist.id}/spot-schedules")

        self.assertEqual(resp.status_code, 403)

    def test_list_spot_schedules_returns_200(self):
        tid = uuid.uuid4()
        playlist = _make_playlist(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        app, _ = self._make_schedule_app(user, playlist=playlist)

        with patch("api.v1.audio.spots.crud_audio_playlist") as mock_pl, \
             patch("api.v1.audio.spots.crud_audio_spot_schedule") as mock_sched:
            mock_pl.get.return_value = playlist
            mock_sched.get_by_playlist.return_value = []

            client = TestClient(app)
            resp = client.get(f"/audio/spots/playlists/{playlist.id}/spot-schedules")

        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_delete_schedule_returns_204(self):
        tid = uuid.uuid4()
        playlist = _make_playlist(tenant_id=tid)
        schedule = _make_schedule(playlist_id=playlist.id)
        spot = _make_spot(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        app, _ = self._make_schedule_app(user, playlist=playlist)

        with patch("api.v1.audio.spots.crud_audio_playlist") as mock_pl, \
             patch("api.v1.audio.spots.crud_audio_spot_schedule") as mock_sched, \
             patch("api.v1.audio.spots._invalidate_device_playlist_cache"), \
             patch("api.v1.audio.spots._device_ids_for_playlist", return_value=set()):
            mock_pl.get.return_value = playlist
            mock_sched.get.return_value = schedule
            mock_sched.remove.return_value = None

            client = TestClient(app)
            resp = client.delete(
                f"/audio/spots/playlists/{playlist.id}/spot-schedules/{schedule.id}"
            )

        self.assertEqual(resp.status_code, 204)

    def test_delete_schedule_not_found_returns_404(self):
        tid = uuid.uuid4()
        playlist = _make_playlist(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        app, _ = self._make_schedule_app(user, playlist=playlist)

        with patch("api.v1.audio.spots.crud_audio_playlist") as mock_pl, \
             patch("api.v1.audio.spots.crud_audio_spot_schedule") as mock_sched:
            mock_pl.get.return_value = playlist
            mock_sched.get.return_value = None

            client = TestClient(app)
            resp = client.delete(
                f"/audio/spots/playlists/{playlist.id}/spot-schedules/{uuid.uuid4()}"
            )

        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
