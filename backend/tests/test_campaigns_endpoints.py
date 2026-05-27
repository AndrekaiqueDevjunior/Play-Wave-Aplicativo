"""Testes CAMPAIGNS — Validação completa de todos os endpoints de campanhas.

Cobre:
  - GET  /campaigns/                   → lista (admin/operator/filtros)
  - GET  /campaigns/statistics/overview → estrutura
  - GET  /campaigns/active/list        → retorna lista
  - GET  /campaigns/scheduled/list     → retorna lista
  - GET  /campaigns/by-priority/list   → retorna lista
  - GET  /campaigns/by-device/{id}     → filtra por device
  - GET  /campaigns/by-media/{id}      → filtra por media
  - GET  /campaigns/{id}               → 200/403/404
  - POST /campaigns/                   → cria campanha
  - PUT  /campaigns/{id}               → atualiza
  - DELETE /campaigns/{id}             → 200/403/404
  - PATCH /campaigns/{id}/status       → muda status
  - POST  /campaigns/{id}/increment-views → incrementa
  - POST  /campaigns/{id}/publish      → → active
  - POST  /campaigns/{id}/pause        → → paused
  - POST  /campaigns/{id}/resume       → → active
  - GET   /campaigns/{id}/stats        → estrutura completa
  - GET   /campaigns/{id}/items        → lista itens de playlist
"""

import unittest
import uuid
from datetime import datetime
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


def _make_campaign(**kw):
    tid = uuid.uuid4()
    base = dict(
        id=uuid.uuid4(),
        tenant_id=tid,
        name="Campanha Teste",
        description=None,
        status="draft",
        priority=1,
        config_version="1",
        device_ids=[],
        media_ids=[],
        media_order=None,
        total_views=0,
        audio_policy=None,
        audio_playlist_id=None,
        audio_playlist=None,
        tags=None,
        is_active=True,
        starts_at=None,
        ends_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _make_playlist_item(**kw):
    base = dict(
        id=uuid.uuid4(),
        campaign_id=uuid.uuid4(),
        media_id=uuid.uuid4(),
        order_index=10,
        display_duration_seconds=30,
        starts_at=None,
        ends_at=None,
        is_active=True,
        repeat_count=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _campaigns_app(user, fake_db=None):
    from api.v1.campaigns import router as campaigns_router
    from core.database import get_db
    from core.dependencies import get_current_user

    app = FastAPI()
    app.include_router(campaigns_router)

    if fake_db is None:
        fake_db = MagicMock()
        fake_db.query.return_value.filter.return_value = fake_db.query.return_value
        fake_db.query.return_value.all.return_value = []
        fake_db.query.return_value.first.return_value = None
        fake_db.query.return_value.count.return_value = 0
        fake_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


LIFECYCLE_PATCHES = [
    "api.v1.campaigns._invalidate_device_playlist_cache",
    "api.v1.campaigns._broadcast_playlist_invalidated",
    "api.v1.campaigns._campaign_device_cache_keys",
]


# ── GET / ─────────────────────────────────────────────────────────────────────

class TestCampaignList(unittest.TestCase):
    def test_list_returns_200(self):
        client = _campaigns_app(_make_user())
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get_multi.return_value = []
            resp = client.get("/campaigns/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_list_with_search_returns_200(self):
        client = _campaigns_app(_make_user())
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.search.return_value = []
            resp = client.get("/campaigns/?search=black+friday")
        self.assertEqual(resp.status_code, 200)

    def test_list_with_status_filter_returns_200(self):
        client = _campaigns_app(_make_user())
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get_by_status.return_value = []
            resp = client.get("/campaigns/?status=active")
        self.assertEqual(resp.status_code, 200)

    def test_operator_sees_only_own_tenant(self):
        tid = uuid.uuid4()
        c = _make_campaign(tenant_id=tid)
        other = _make_campaign(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=tid)
        client = _campaigns_app(user)
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get_by_tenant.return_value = [c, other]
            resp = client.get("/campaigns/")
        data = resp.json()
        self.assertEqual(len(data), 1)


# ── GET /statistics/overview ──────────────────────────────────────────────────

class TestCampaignStatistics(unittest.TestCase):
    def test_statistics_returns_200(self):
        client = _campaigns_app(_make_user())
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get_statistics.return_value = {
                "total": 5, "active": 2, "paused": 1, "draft": 2,
            }
            resp = client.get("/campaigns/statistics/overview")
        self.assertEqual(resp.status_code, 200)


# ── GET /active/list, /scheduled/list, /by-priority/list ─────────────────────

class TestCampaignFilteredLists(unittest.TestCase):
    def test_active_list_returns_200(self):
        client = _campaigns_app(_make_user())
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get_active.return_value = []
            resp = client.get("/campaigns/active/list")
        self.assertEqual(resp.status_code, 200)

    def test_scheduled_list_returns_200(self):
        client = _campaigns_app(_make_user())
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get_scheduled.return_value = []
            resp = client.get("/campaigns/scheduled/list")
        self.assertEqual(resp.status_code, 200)

    def test_by_priority_list_returns_200(self):
        client = _campaigns_app(_make_user())
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get_by_priority.return_value = []
            resp = client.get("/campaigns/by-priority/list")
        self.assertEqual(resp.status_code, 200)

    def test_by_device_returns_200(self):
        client = _campaigns_app(_make_user())
        did = uuid.uuid4()
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get_by_device.return_value = []
            resp = client.get(f"/campaigns/by-device/{did}")
        self.assertEqual(resp.status_code, 200)

    def test_by_media_returns_200(self):
        client = _campaigns_app(_make_user())
        mid = uuid.uuid4()
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get_by_media.return_value = []
            resp = client.get(f"/campaigns/by-media/{mid}")
        self.assertEqual(resp.status_code, 200)


# ── GET /{id} ─────────────────────────────────────────────────────────────────

class TestCampaignGetById(unittest.TestCase):
    def test_get_existing_returns_200(self):
        tid = uuid.uuid4()
        c = _make_campaign(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        client = _campaigns_app(user)
        # crud_audio_playlist is imported locally inside the function;
        # patch it at its source module level instead
        with patch("api.v1.campaigns.crud_campaign") as m, \
             patch("crud.entidades.crud_audio_playlist.crud_audio_playlist"):
            m.get.return_value = c
            resp = client.get(f"/campaigns/{c.id}")
        self.assertEqual(resp.status_code, 200)

    def test_get_not_found_returns_404(self):
        client = _campaigns_app(_make_user())
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get.return_value = None
            resp = client.get(f"/campaigns/{NULL_UUID}")
        self.assertEqual(resp.status_code, 404)

    def test_get_cross_tenant_returns_403(self):
        c = _make_campaign(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        client = _campaigns_app(user)
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get.return_value = c
            resp = client.get(f"/campaigns/{c.id}")
        self.assertEqual(resp.status_code, 403)


# ── POST / ────────────────────────────────────────────────────────────────────

class TestCampaignCreate(unittest.TestCase):
    def test_create_returns_201_or_200(self):
        tid = uuid.uuid4()
        c = _make_campaign(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        client = _campaigns_app(user)
        with patch("api.v1.campaigns.crud_campaign") as m, \
             patch("api.v1.campaigns._validate_campaign_device_ids", return_value=[]), \
             patch("api.v1.campaigns._validate_campaign_media_refs", return_value=([], None)):
            m.create.return_value = c
            resp = client.post("/campaigns/", json={
                "name": "Nova Campanha",
                "tenant_id": str(tid),
            })
        self.assertIn(resp.status_code, (200, 201))

    def test_create_missing_name_returns_422(self):
        client = _campaigns_app(_make_user())
        resp = client.post("/campaigns/", json={})
        self.assertEqual(resp.status_code, 422)


# ── PUT /{id} ─────────────────────────────────────────────────────────────────

class TestCampaignUpdate(unittest.TestCase):
    def test_update_returns_200(self):
        tid = uuid.uuid4()
        c = _make_campaign(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        client = _campaigns_app(user)
        with patch("api.v1.campaigns.crud_campaign") as m, \
             patch("api.v1.campaigns._validate_campaign_device_ids", return_value=[]), \
             patch("api.v1.campaigns._validate_campaign_media_refs", return_value=([], None)), \
             patch("api.v1.campaigns._invalidate_device_playlist_cache"), \
             patch("api.v1.campaigns._broadcast_playlist_invalidated"), \
             patch("api.v1.campaigns._campaign_device_cache_keys", return_value=set()):
            m.get.return_value = c
            m.update.return_value = c
            m.increment_config_version.return_value = c
            resp = client.put(f"/campaigns/{c.id}", json={"name": "Novo Nome"})
        self.assertEqual(resp.status_code, 200)

    def test_update_not_found_returns_404(self):
        client = _campaigns_app(_make_user())
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get.return_value = None
            resp = client.put(f"/campaigns/{NULL_UUID}", json={"name": "X"})
        self.assertEqual(resp.status_code, 404)

    def test_update_cross_tenant_returns_403(self):
        c = _make_campaign(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        client = _campaigns_app(user)
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get.return_value = c
            resp = client.put(f"/campaigns/{c.id}", json={"name": "X"})
        self.assertEqual(resp.status_code, 403)


# ── DELETE /{id} ──────────────────────────────────────────────────────────────

class TestCampaignDelete(unittest.TestCase):
    def test_delete_not_found_returns_404(self):
        client = _campaigns_app(_make_user())
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get.return_value = None
            resp = client.delete(f"/campaigns/{NULL_UUID}")
        self.assertEqual(resp.status_code, 404)

    def test_delete_cross_tenant_returns_403(self):
        c = _make_campaign(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        client = _campaigns_app(user)
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get.return_value = c
            resp = client.delete(f"/campaigns/{c.id}")
        self.assertEqual(resp.status_code, 403)

    def test_delete_existing_returns_200(self):
        tid = uuid.uuid4()
        c = _make_campaign(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        client = _campaigns_app(user)
        with patch("api.v1.campaigns.crud_campaign") as m, \
             patch("api.v1.campaigns._invalidate_device_playlist_cache"), \
             patch("api.v1.campaigns._broadcast_playlist_invalidated"), \
             patch("api.v1.campaigns._campaign_device_cache_keys", return_value=set()):
            m.get.return_value = c
            m.remove.return_value = c
            resp = client.delete(f"/campaigns/{c.id}")
        self.assertEqual(resp.status_code, 200)


# ── PATCH /{id}/status ────────────────────────────────────────────────────────

class TestCampaignPatchStatus(unittest.TestCase):
    def test_patch_status_returns_200(self):
        tid = uuid.uuid4()
        c = _make_campaign(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        client = _campaigns_app(user)
        with patch("api.v1.campaigns.crud_campaign") as m, \
             patch("api.v1.campaigns._invalidate_device_playlist_cache"), \
             patch("api.v1.campaigns._broadcast_playlist_invalidated"), \
             patch("api.v1.campaigns._campaign_device_cache_keys", return_value=set()):
            m.get.return_value = c
            m.update_status.return_value = c
            m.increment_config_version.return_value = c
            resp = client.patch(f"/campaigns/{c.id}/status?status=active")
        self.assertEqual(resp.status_code, 200)

    def test_patch_status_not_found_returns_404(self):
        client = _campaigns_app(_make_user())
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get.return_value = None
            resp = client.patch(f"/campaigns/{NULL_UUID}/status?status=active")
        self.assertEqual(resp.status_code, 404)

    def test_patch_status_invalid_value_returns_422(self):
        client = _campaigns_app(_make_user())
        resp = client.patch(f"/campaigns/{NULL_UUID}/status?status=nao_existe")
        self.assertEqual(resp.status_code, 422)


# ── POST /{id}/increment-views ────────────────────────────────────────────────

class TestCampaignIncrementViews(unittest.TestCase):
    def test_increment_views_returns_200(self):
        tid = uuid.uuid4()
        c = _make_campaign(tenant_id=tid, total_views=5)
        user = _make_user(role="admin", tenant_id=tid)
        client = _campaigns_app(user)
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get.return_value = c
            m.increment_views.return_value = SimpleNamespace(**{**c.__dict__, "total_views": 6})
            resp = client.post(f"/campaigns/{c.id}/increment-views")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("total_views", resp.json())

    def test_increment_views_not_found_returns_404(self):
        client = _campaigns_app(_make_user())
        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get.return_value = None
            resp = client.post(f"/campaigns/{NULL_UUID}/increment-views")
        self.assertEqual(resp.status_code, 404)


# ── POST /{id}/publish, /pause, /resume ──────────────────────────────────────

class TestCampaignLifecycleEndpoints(unittest.TestCase):
    def _call(self, action, campaign, user, *, found=True):
        app = FastAPI()
        from api.v1.campaigns import router as campaigns_router
        from core.database import get_db
        from core.dependencies import get_current_user

        app.include_router(campaigns_router)
        app.dependency_overrides[get_db] = lambda: MagicMock()
        app.dependency_overrides[get_current_user] = lambda: user

        with patch("api.v1.campaigns.crud_campaign") as m, \
             patch("api.v1.campaigns._invalidate_device_playlist_cache"), \
             patch("api.v1.campaigns._broadcast_playlist_invalidated"), \
             patch("api.v1.campaigns._campaign_device_cache_keys", return_value=set()):
            m.get.return_value = campaign if found else None
            m.update.return_value = campaign
            m.increment_config_version.return_value = campaign
            client = TestClient(app)
            return client.post(f"/campaigns/{campaign.id}/{action}")

    def test_publish_same_tenant_returns_200(self):
        tid = uuid.uuid4()
        resp = self._call("publish", _make_campaign(tenant_id=tid), _make_user(tenant_id=tid))
        self.assertEqual(resp.status_code, 200)

    def test_pause_same_tenant_returns_200(self):
        tid = uuid.uuid4()
        resp = self._call("pause", _make_campaign(tenant_id=tid), _make_user(tenant_id=tid))
        self.assertEqual(resp.status_code, 200)

    def test_resume_same_tenant_returns_200(self):
        tid = uuid.uuid4()
        resp = self._call("resume", _make_campaign(tenant_id=tid), _make_user(tenant_id=tid))
        self.assertEqual(resp.status_code, 200)

    def test_publish_not_found_returns_404(self):
        resp = self._call("publish", _make_campaign(), _make_user(), found=False)
        self.assertEqual(resp.status_code, 404)

    def test_publish_cross_tenant_returns_403(self):
        resp = self._call(
            "publish",
            _make_campaign(tenant_id=uuid.uuid4()),
            _make_user(role="operator", tenant_id=uuid.uuid4()),
        )
        self.assertEqual(resp.status_code, 403)


# ── GET /{id}/stats ───────────────────────────────────────────────────────────

class TestCampaignStats(unittest.TestCase):
    def _call_stats(self, campaign, user, *, found=True):
        from api.v1.campaigns import router as campaigns_router
        from core.database import get_db
        from core.dependencies import get_current_user

        app = FastAPI()
        app.include_router(campaigns_router)
        fake_db = MagicMock()
        fake_db.query.return_value.filter.return_value.count.return_value = 0
        app.dependency_overrides[get_db] = lambda: fake_db
        app.dependency_overrides[get_current_user] = lambda: user

        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get.return_value = campaign if found else None
            return TestClient(app).get(f"/campaigns/{campaign.id}/stats")

    def test_stats_has_expected_keys(self):
        tid = uuid.uuid4()
        resp = self._call_stats(_make_campaign(tenant_id=tid), _make_user(tenant_id=tid))
        self.assertEqual(resp.status_code, 200)
        for key in ("id", "name", "status", "device_count", "media_count", "total_views", "playback_count"):
            self.assertIn(key, resp.json(), f"Chave '{key}' ausente em /stats")

    def test_stats_not_found_returns_404(self):
        resp = self._call_stats(_make_campaign(), _make_user(), found=False)
        self.assertEqual(resp.status_code, 404)

    def test_stats_cross_tenant_returns_403(self):
        resp = self._call_stats(
            _make_campaign(tenant_id=uuid.uuid4()),
            _make_user(role="operator", tenant_id=uuid.uuid4()),
        )
        self.assertEqual(resp.status_code, 403)


# ── GET /{id}/items ───────────────────────────────────────────────────────────

class TestCampaignItems(unittest.TestCase):
    def test_items_list_returns_200(self):
        tid = uuid.uuid4()
        c = _make_campaign(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)

        from api.v1.campaigns import router as campaigns_router
        from core.database import get_db
        from core.dependencies import get_current_user

        app = FastAPI()
        app.include_router(campaigns_router)
        fake_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: fake_db
        app.dependency_overrides[get_current_user] = lambda: user

        with patch("api.v1.campaigns.crud_campaign") as mc, \
             patch("api.v1.campaigns.crud_campaign_playlist_item") as mi:
            mc.get.return_value = c
            mi.list_by_campaign.return_value = []
            resp = TestClient(app).get(f"/campaigns/{c.id}/items")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_items_not_found_returns_404(self):
        from api.v1.campaigns import router as campaigns_router
        from core.database import get_db
        from core.dependencies import get_current_user

        app = FastAPI()
        app.include_router(campaigns_router)
        app.dependency_overrides[get_db] = lambda: MagicMock()
        app.dependency_overrides[get_current_user] = lambda: _make_user()

        with patch("api.v1.campaigns.crud_campaign") as m:
            m.get.return_value = None
            resp = TestClient(app).get(f"/campaigns/{NULL_UUID}/items")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
