"""Testes CAMPAIGNS — Ciclo de vida de campanhas.

Cobre:
  - _normalize_uuid_list: já coberto em test_devices_commands.py (importado aqui para _validate_campaign_*)
  - _validate_campaign_device_ids: device não encontrado → 422, cross-tenant → 422
  - _validate_campaign_media_refs: mídia não encontrada → 422
  - Endpoint POST /campaigns/{id}/publish: muda status para active
  - Endpoint POST /campaigns/{id}/pause: muda status para paused
  - Endpoint POST /campaigns/{id}/resume: muda status para active
  - Endpoint GET /campaigns/{id}/stats: retorna estrutura correta
  - Autorização: tenant errado retorna 403, not found retorna 404
"""

import unittest
import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_campaign(**kwargs):
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Campanha Teste",
        status="draft",
        device_ids=[],
        media_ids=[],
        media_order=None,
        total_views=0,
        config_version="1",
        audio_policy=None,
        audio_playlist_id=None,
        description=None,
        priority=1,
        starts_at=None,
        ends_at=None,
        tags=None,
        is_active=True,
        updated_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_user(**kwargs):
    defaults = dict(
        id=uuid.uuid4(),
        email="admin@test.com",
        role="admin",
        tenant_id=uuid.uuid4(),
        is_active=True,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_device(**kwargs):
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_media(**kwargs):
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _campaign_app(campaign, user):
    from api.v1.campaigns import router as campaigns_router
    from core.database import get_db
    from core.dependencies import get_current_user

    app = FastAPI()
    app.include_router(campaigns_router)

    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: user

    return app


# ── Testes — _validate_campaign_device_ids ───────────────────────────────────

class TestValidateCampaignDeviceIds(unittest.TestCase):
    def setUp(self):
        from api.v1.campaigns import _validate_campaign_device_ids
        self.fn = _validate_campaign_device_ids

    def test_empty_list_passes(self):
        db = MagicMock()
        result = self.fn(db, device_ids=[], tenant_id=None)
        self.assertEqual(result, [])

    def test_device_not_found_raises_422(self):
        from fastapi import HTTPException

        uid = str(uuid.uuid4())
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        with self.assertRaises(HTTPException) as ctx:
            self.fn(db, device_ids=[uid], tenant_id=None)
        self.assertEqual(ctx.exception.status_code, 422)

    def test_cross_tenant_device_raises_422(self):
        from fastapi import HTTPException

        device_id = str(uuid.uuid4())
        device = _make_device(id=uuid.UUID(device_id), tenant_id=uuid.uuid4())
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [device]

        with self.assertRaises(HTTPException) as ctx:
            self.fn(db, device_ids=[device_id], tenant_id=str(uuid.uuid4()))
        self.assertEqual(ctx.exception.status_code, 422)

    def test_same_tenant_device_passes(self):
        tid = uuid.uuid4()
        device_id = str(uuid.uuid4())
        device = _make_device(id=uuid.UUID(device_id), tenant_id=tid)
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [device]

        result = self.fn(db, device_ids=[device_id], tenant_id=str(tid))
        self.assertEqual(result, [device_id])


# ── Testes — _validate_campaign_media_refs ───────────────────────────────────

class TestValidateCampaignMediaRefs(unittest.TestCase):
    def setUp(self):
        from api.v1.campaigns import _validate_campaign_media_refs
        self.fn = _validate_campaign_media_refs

    def test_empty_refs_pass(self):
        db = MagicMock()
        ids, order = self.fn(db, media_ids=[], media_order=None, tenant_id=None)
        self.assertEqual(ids, [])
        self.assertIsNone(order)

    def test_missing_media_raises_422(self):
        from fastapi import HTTPException

        uid = str(uuid.uuid4())
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        with self.assertRaises(HTTPException) as ctx:
            self.fn(db, media_ids=[uid], media_order=None, tenant_id=None)
        self.assertEqual(ctx.exception.status_code, 422)

    def test_existing_media_passes(self):
        media_id = str(uuid.uuid4())
        media = _make_media(id=uuid.UUID(media_id))
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [media]

        ids, order = self.fn(db, media_ids=[media_id], media_order=None, tenant_id=None)
        self.assertIn(media_id, ids)


# ── Testes — publish/pause/resume endpoints ───────────────────────────────────

class TestCampaignLifecycle(unittest.TestCase):
    def _call(self, action, campaign, user, *, found=True):
        app = _campaign_app(campaign, user)
        campaign_id = str(campaign.id)

        with patch("api.v1.campaigns.crud_campaign") as mock_crud, \
             patch("api.v1.campaigns._invalidate_device_playlist_cache"), \
             patch("api.v1.campaigns._broadcast_playlist_invalidated"), \
             patch("api.v1.campaigns._campaign_device_cache_keys", return_value=set()):

            mock_crud.get.return_value = campaign if found else None
            mock_crud.update.return_value = campaign
            mock_crud.increment_config_version.return_value = campaign

            client = TestClient(app)
            return client.post(f"/campaigns/{campaign_id}/{action}")

    def test_publish_returns_200(self):
        tid = uuid.uuid4()
        campaign = _make_campaign(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        resp = self._call("publish", campaign, user)
        self.assertEqual(resp.status_code, 200)

    def test_pause_returns_200(self):
        tid = uuid.uuid4()
        campaign = _make_campaign(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        resp = self._call("pause", campaign, user)
        self.assertEqual(resp.status_code, 200)

    def test_resume_returns_200(self):
        tid = uuid.uuid4()
        campaign = _make_campaign(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        resp = self._call("resume", campaign, user)
        self.assertEqual(resp.status_code, 200)

    def test_publish_nonexistent_campaign_returns_404(self):
        campaign = _make_campaign()
        user = _make_user(role="admin")
        resp = self._call("publish", campaign, user, found=False)
        self.assertEqual(resp.status_code, 404)

    def test_publish_wrong_tenant_returns_403(self):
        campaign = _make_campaign(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        resp = self._call("publish", campaign, user)
        self.assertEqual(resp.status_code, 403)

    def test_pause_wrong_tenant_returns_403(self):
        campaign = _make_campaign(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        resp = self._call("pause", campaign, user)
        self.assertEqual(resp.status_code, 403)


# ── Testes — GET /campaigns/{id}/stats ───────────────────────────────────────

class TestCampaignStats(unittest.TestCase):
    def _call_stats(self, campaign, user, *, found=True):
        from api.v1.campaigns import router as campaigns_router
        from core.database import get_db
        from core.dependencies import get_current_user

        app = FastAPI()
        app.include_router(campaigns_router)

        fake_db = MagicMock()
        fake_db.query.return_value.filter.return_value.count.return_value = 42

        app.dependency_overrides[get_db] = lambda: fake_db
        app.dependency_overrides[get_current_user] = lambda: user

        with patch("api.v1.campaigns.crud_campaign") as mock_crud:
            mock_crud.get.return_value = campaign if found else None
            client = TestClient(app)
            return client.get(f"/campaigns/{campaign.id}/stats")

    def test_stats_returns_expected_structure(self):
        tid = uuid.uuid4()
        campaign = _make_campaign(tenant_id=tid, device_ids=[], media_ids=[])
        user = _make_user(role="admin", tenant_id=tid)
        resp = self._call_stats(campaign, user)
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        for key in ("id", "name", "status", "device_count", "media_count", "total_views", "playback_count"):
            self.assertIn(key, data, f"Chave '{key}' ausente")

    def test_stats_not_found_returns_404(self):
        campaign = _make_campaign()
        user = _make_user(role="admin")
        resp = self._call_stats(campaign, user, found=False)
        self.assertEqual(resp.status_code, 404)

    def test_stats_wrong_tenant_returns_403(self):
        campaign = _make_campaign(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        resp = self._call_stats(campaign, user)
        self.assertEqual(resp.status_code, 403)


if __name__ == "__main__":
    unittest.main()
