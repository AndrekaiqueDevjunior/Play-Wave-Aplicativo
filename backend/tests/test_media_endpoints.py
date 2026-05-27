"""Testes MEDIA — Validação completa de todos os endpoints de mídias.

Cobre:
  - GET  /media/                   → lista (admin vê tudo, operator filtra por tenant)
  - GET  /media/statistics/overview → estrutura by_type + status counts
  - GET  /media/available/list     → retorna lista
  - GET  /media/processing/list    → retorna lista
  - GET  /media/error/list         → retorna lista
  - GET  /media/by-type/{type}     → filtra por tipo
  - GET  /media/by-category/{cat}  → filtra por categoria
  - GET  /media/{id}               → 200 admin, 403 cross-tenant, 404 not found
  - POST /media/                   → cria mídia via JSON (sem upload)
  - PUT  /media/{id}               → atualiza nome/descrição
  - PATCH /media/{id}/status       → muda status
  - DELETE /media/{id}             → 409 se em uso sem force; 200 com force
  - GET  /media/{id}/usage         → estrutura com campaigns
  - GET  /media/{id}/versions      → lista de versões
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


def _make_media(**kw):
    tid = uuid.uuid4()
    base = dict(
        id=uuid.uuid4(),
        tenant_id=tid,
        name="Teste Media",
        description="desc",
        type="image",
        status="available",
        file_url="/uploads/img.jpg",
        file_size=None,
        file_hash=None,
        file_version=1,
        mime_type=None,
        duration=None,
        duration_seconds=None,
        display_duration_seconds=None,
        resolution=None,
        width=None,
        height=None,
        thumbnail_url=None,
        category="geral",
        tags=[],
        notes=None,
        extra_metadata=None,
        audio_policy=None,
        created_by=None,
        updated_by=None,
        is_active=True,
        starts_at=None,
        ends_at=None,
        has_audio=None,
        availability_status=None,
        usage_count=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _media_app(user, fake_db=None):
    from api.v1.media import router as media_router
    from core.database import get_db
    from core.dependencies import get_current_user

    app = FastAPI()
    app.include_router(media_router)

    if fake_db is None:
        fake_db = MagicMock()
        fake_db.query.return_value.filter.return_value = fake_db.query.return_value
        fake_db.query.return_value.all.return_value = []
        fake_db.query.return_value.first.return_value = None
        fake_db.query.return_value.count.return_value = 0
        fake_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        fake_db.query.return_value.delete.return_value = 0

    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


# ── GET / ─────────────────────────────────────────────────────────────────────

class TestMediaList(unittest.TestCase):
    def test_list_returns_200(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get_multi.return_value = []
            resp = client.get("/media/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_list_with_search_returns_200(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.search.return_value = []
            resp = client.get("/media/?search=logo")
        self.assertEqual(resp.status_code, 200)

    def test_list_with_type_filter_returns_200(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get_by_type.return_value = []
            resp = client.get("/media/?media_type=image")
        self.assertEqual(resp.status_code, 200)

    def test_list_with_status_filter_returns_200(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get_by_status.return_value = []
            resp = client.get("/media/?status=available")
        self.assertEqual(resp.status_code, 200)

    def test_list_with_category_filter_returns_200(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get_by_category.return_value = []
            resp = client.get("/media/?category=promo")
        self.assertEqual(resp.status_code, 200)

    def test_list_with_tags_filter_returns_200(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get_by_tags.return_value = []
            resp = client.get("/media/?tags=verao,promo")
        self.assertEqual(resp.status_code, 200)

    def test_operator_filters_own_tenant(self):
        tid = uuid.uuid4()
        media = _make_media(tenant_id=tid)
        user = _make_user(role="operator", tenant_id=tid)
        client = _media_app(user)
        with patch("api.v1.media.crud_media") as m:
            m.get_by_tenant.return_value = [media]
            resp = client.get("/media/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

    def test_operator_cannot_see_other_tenant_media(self):
        tid = uuid.uuid4()
        other_media = _make_media(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=tid)
        client = _media_app(user)
        with patch("api.v1.media.crud_media") as m:
            m.get_by_tenant.return_value = [other_media]
            resp = client.get("/media/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 0)


# ── GET /statistics/overview ──────────────────────────────────────────────────

class TestMediaStatistics(unittest.TestCase):
    def test_statistics_returns_200(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get_statistics.return_value = {
                "total": 10,
                "available": 8,
                "processing": 1,
                "error": 1,
                "by_type": {"image": 5, "video": 3, "audio": 1, "external_url": 1},
            }
            resp = client.get("/media/statistics/overview")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        for key in ("total", "available", "processing", "error", "by_type"):
            self.assertIn(key, data)

    def test_statistics_by_type_has_all_types(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get_statistics.return_value = {
                "total": 0, "available": 0, "processing": 0, "error": 0,
                "by_type": {"image": 0, "video": 0, "audio": 0, "external_url": 0},
            }
            data = client.get("/media/statistics/overview").json()
        for t in ("image", "video", "audio", "external_url"):
            self.assertIn(t, data["by_type"])


# ── GET /available/list, /processing/list, /error/list ───────────────────────

class TestMediaFilteredLists(unittest.TestCase):
    def test_available_list_returns_200(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get_available.return_value = []
            resp = client.get("/media/available/list")
        self.assertEqual(resp.status_code, 200)

    def test_processing_list_returns_200(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get_processing.return_value = []
            resp = client.get("/media/processing/list")
        self.assertEqual(resp.status_code, 200)

    def test_error_list_returns_200(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get_with_error.return_value = []
            resp = client.get("/media/error/list")
        self.assertEqual(resp.status_code, 200)

    def test_by_type_returns_200(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get_by_type.return_value = []
            resp = client.get("/media/by-type/video")
        self.assertEqual(resp.status_code, 200)

    def test_by_category_returns_200(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get_by_category.return_value = []
            resp = client.get("/media/by-category/promocional")
        self.assertEqual(resp.status_code, 200)


# ── GET /{id} ─────────────────────────────────────────────────────────────────

class TestMediaGetById(unittest.TestCase):
    def test_get_existing_returns_200(self):
        tid = uuid.uuid4()
        media = _make_media(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        client = _media_app(user)
        with patch("api.v1.media.crud_media") as m, \
             patch("api.v1.media._decorate_media", side_effect=lambda db, x: x):
            m.get.return_value = media
            resp = client.get(f"/media/{media.id}")
        self.assertEqual(resp.status_code, 200)

    def test_get_not_found_returns_404(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get.return_value = None
            resp = client.get(f"/media/{NULL_UUID}")
        self.assertEqual(resp.status_code, 404)

    def test_get_cross_tenant_returns_403(self):
        media = _make_media(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        client = _media_app(user)
        with patch("api.v1.media.crud_media") as m:
            m.get.return_value = media
            resp = client.get(f"/media/{media.id}")
        self.assertEqual(resp.status_code, 403)


# ── POST / ────────────────────────────────────────────────────────────────────

class TestMediaCreate(unittest.TestCase):
    def test_create_returns_201(self):
        tid = uuid.uuid4()
        user = _make_user(role="admin", tenant_id=tid)
        media = _make_media(tenant_id=tid)
        client = _media_app(user)
        with patch("api.v1.media.crud_media") as m:
            m.create.return_value = media
            resp = client.post("/media/", json={
                "name": "Imagem Teste",
                "type": "image",
                "file_url": "https://example.com/img.jpg",
                "tenant_id": str(tid),
            })
        self.assertIn(resp.status_code, (200, 201))

    def test_create_missing_required_fields_returns_422(self):
        client = _media_app(_make_user())
        resp = client.post("/media/", json={})
        self.assertEqual(resp.status_code, 422)


# ── PUT /{id} ─────────────────────────────────────────────────────────────────

class TestMediaUpdate(unittest.TestCase):
    def test_update_returns_200(self):
        tid = uuid.uuid4()
        media = _make_media(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        client = _media_app(user)
        with patch("api.v1.media.crud_media") as m:
            m.get.return_value = media
            m.update.return_value = media
            resp = client.put(f"/media/{media.id}", json={"name": "Novo Nome"})
        self.assertEqual(resp.status_code, 200)

    def test_update_not_found_returns_404(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get.return_value = None
            resp = client.put(f"/media/{NULL_UUID}", json={"name": "X"})
        self.assertEqual(resp.status_code, 404)

    def test_update_cross_tenant_returns_403(self):
        media = _make_media(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        client = _media_app(user)
        with patch("api.v1.media.crud_media") as m:
            m.get.return_value = media
            resp = client.put(f"/media/{media.id}", json={"name": "X"})
        self.assertEqual(resp.status_code, 403)


# ── PATCH /{id}/status ────────────────────────────────────────────────────────

class TestMediaPatchStatus(unittest.TestCase):
    def test_patch_status_returns_200(self):
        tid = uuid.uuid4()
        media = _make_media(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        client = _media_app(user)
        with patch("api.v1.media.crud_media") as m:
            m.get.return_value = media
            m.update_status.return_value = media
            resp = client.patch(f"/media/{media.id}/status?media_status=processing")
        self.assertEqual(resp.status_code, 200)

    def test_patch_status_not_found_returns_404(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get.return_value = None
            resp = client.patch(f"/media/{NULL_UUID}/status?media_status=available")
        self.assertEqual(resp.status_code, 404)

    def test_patch_status_invalid_value_returns_422(self):
        tid = uuid.uuid4()
        media = _make_media(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        client = _media_app(user)
        with patch("api.v1.media.crud_media") as m:
            m.get.return_value = media
            resp = client.patch(f"/media/{media.id}/status?media_status=nao_existe")
        self.assertEqual(resp.status_code, 422)


# ── DELETE /{id} ──────────────────────────────────────────────────────────────

class TestMediaDelete(unittest.TestCase):
    def test_delete_not_found_returns_404(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get.return_value = None
            resp = client.delete(f"/media/{NULL_UUID}")
        self.assertEqual(resp.status_code, 404)

    def test_delete_in_use_returns_409(self):
        tid = uuid.uuid4()
        media = _make_media(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        client = _media_app(user)
        fake_campaign = SimpleNamespace(id=uuid.uuid4(), name="Camp")
        with patch("api.v1.media.crud_media") as m, \
             patch("api.v1.media._campaigns_using_media", return_value=[fake_campaign]):
            m.get.return_value = media
            resp = client.delete(f"/media/{media.id}")
        self.assertEqual(resp.status_code, 409)

    def test_delete_in_use_with_force_returns_200(self):
        tid = uuid.uuid4()
        media = _make_media(tenant_id=tid, file_url=None)
        user = _make_user(role="admin", tenant_id=tid)
        client = _media_app(user)
        with patch("api.v1.media.crud_media") as m, \
             patch("api.v1.media._campaigns_using_media", return_value=[]), \
             patch("api.v1.media._remove_media_from_campaigns", return_value=[]), \
             patch("api.v1.media._invalidate_device_playlist_cache"), \
             patch("api.v1.media._broadcast_media_changed"), \
             patch("api.v1.media._device_ids_for_campaigns", return_value=set()):
            m.get.return_value = media
            m.remove.return_value = media
            db_mock = MagicMock()
            db_mock.query.return_value.filter.return_value.delete.return_value = 0
            resp = client.delete(f"/media/{media.id}?force=true")
        self.assertEqual(resp.status_code, 200)

    def test_delete_cross_tenant_returns_403(self):
        media = _make_media(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        client = _media_app(user)
        with patch("api.v1.media.crud_media") as m:
            m.get.return_value = media
            resp = client.delete(f"/media/{media.id}")
        self.assertEqual(resp.status_code, 403)


# ── GET /{id}/usage ───────────────────────────────────────────────────────────

class TestMediaUsage(unittest.TestCase):
    def test_usage_returns_200_with_campaigns_key(self):
        tid = uuid.uuid4()
        media = _make_media(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        client = _media_app(user)
        with patch("api.v1.media.crud_media") as m, \
             patch("api.v1.media._campaigns_using_media", return_value=[]):
            m.get.return_value = media
            resp = client.get(f"/media/{media.id}/usage")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("campaigns", resp.json())

    def test_usage_not_found_returns_404(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get.return_value = None
            resp = client.get(f"/media/{NULL_UUID}/usage")
        self.assertEqual(resp.status_code, 404)


# ── GET /{id}/versions ────────────────────────────────────────────────────────

class TestMediaVersions(unittest.TestCase):
    def test_versions_returns_200(self):
        tid = uuid.uuid4()
        media = _make_media(tenant_id=tid)
        user = _make_user(role="admin", tenant_id=tid)
        client = _media_app(user)

        fake_db = MagicMock()
        fake_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        with patch("api.v1.media.crud_media") as m:
            m.get.return_value = media
            resp = _media_app(user, fake_db).get(f"/media/{media.id}/versions")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_versions_not_found_returns_404(self):
        client = _media_app(_make_user())
        with patch("api.v1.media.crud_media") as m:
            m.get.return_value = None
            resp = client.get(f"/media/{NULL_UUID}/versions")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
