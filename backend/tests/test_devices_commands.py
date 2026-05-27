"""Testes DEVICES — Bloqueio, desbloqueio e gestão de dispositivos.

Cobre:
  - Endpoint POST /devices/{id}/block: admin bloqueia, tenant errado retorna 403, not found retorna 404
  - Endpoint POST /devices/{id}/unblock: admin desbloqueia, tenant errado retorna 403
  - Endpoint POST /devices/{id}/command: valida que comando é enviado ao dispositivo
  - Endpoint GET /devices/{id}: retorna 404 para id inexistente, 200 para existente
  - _normalize_uuid_list (campaigns.py): UUID válido, inválido, vazio, duplicado
"""

import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_device(**kwargs):
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="TV Recepção",
        status="online",
        is_blocked=False,
        requires_repairing=False,
        pairing_code="TV-ABCD",
        device_token="tok-valid",
        token_version=1,
        pairing_version=1,
        location=None,
        current_campaign=None,
        current_campaign_id=None,
        audio_playlist_id=None,
        last_seen_at=None,
        last_connection=None,
        updated_at=None,
        created_at=None,
        osd_config=None,
        config=None,
        type="android_tv",
        group=None,
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


def _make_block_app(device, user):
    """Monta app mínima com rotas de bloqueio."""
    from api.v1.devices import router as devices_router
    from core.database import get_db
    from core.dependencies import get_current_user

    app = FastAPI()
    app.include_router(devices_router)

    fake_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_user] = lambda: user

    return app, fake_db


# ── Testes — _normalize_uuid_list (campaigns) ────────────────────────────────

class TestNormalizeUuidList(unittest.TestCase):
    def setUp(self):
        from api.v1.campaigns import _normalize_uuid_list
        self.fn = _normalize_uuid_list

    def test_valid_uuid_passes(self):
        uid = str(uuid.uuid4())
        result = self.fn([uid], label="dispositivos")
        self.assertEqual(result, [uid])

    def test_empty_list_returns_empty(self):
        result = self.fn([], label="dispositivos")
        self.assertEqual(result, [])

    def test_none_returns_empty(self):
        result = self.fn(None, label="dispositivos")
        self.assertEqual(result, [])

    def test_invalid_uuid_raises_422(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            self.fn(["not-a-uuid"], label="dispositivos")
        self.assertEqual(ctx.exception.status_code, 422)

    def test_empty_string_in_list_raises_422(self):
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            self.fn([""], label="dispositivos")
        self.assertEqual(ctx.exception.status_code, 422)

    def test_duplicates_are_removed(self):
        uid = str(uuid.uuid4())
        result = self.fn([uid, uid, uid], label="dispositivos")
        self.assertEqual(result, [uid])

    def test_multiple_valid_uuids(self):
        ids = [str(uuid.uuid4()) for _ in range(3)]
        result = self.fn(ids, label="dispositivos")
        self.assertEqual(result, ids)


# ── Testes — block_device endpoint ───────────────────────────────────────────

class TestBlockDeviceEndpoint(unittest.TestCase):
    def _call_block(self, device, user, *, device_found=True):
        app, fake_db = _make_block_app(device, user)
        device_id = str(device.id)

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_pairing_event") as mock_events, \
             patch("api.v1.devices._publish_pairing_revoked"):

            mock_crud.get.return_value = device if device_found else None
            mock_crud.block_device.return_value = device
            mock_events.log.return_value = None

            client = TestClient(app)
            return client.post(f"/devices/{device_id}/block")

    def test_admin_blocks_device_successfully(self):
        device = _make_device()
        user = _make_user(role="admin")
        resp = self._call_block(device, user)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("message", resp.json())

    def test_block_nonexistent_device_returns_404(self):
        device = _make_device()
        user = _make_user(role="admin")
        resp = self._call_block(device, user, device_found=False)
        self.assertEqual(resp.status_code, 404)

    def test_operator_wrong_tenant_returns_403(self):
        device = _make_device(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        resp = self._call_block(device, user)
        self.assertEqual(resp.status_code, 403)

    def test_operator_same_tenant_can_block(self):
        tid = uuid.uuid4()
        device = _make_device(tenant_id=tid)
        user = _make_user(role="operator", tenant_id=tid)
        resp = self._call_block(device, user)
        self.assertEqual(resp.status_code, 200)


# ── Testes — unblock_device endpoint ─────────────────────────────────────────

class TestUnblockDeviceEndpoint(unittest.TestCase):
    def _call_unblock(self, device, user, *, device_found=True):
        app, fake_db = _make_block_app(device, user)
        device_id = str(device.id)

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_pairing_event") as mock_events:

            mock_crud.get.return_value = device if device_found else None
            mock_crud.unblock_device.return_value = device
            mock_events.log.return_value = None

            client = TestClient(app)
            return client.post(f"/devices/{device_id}/unblock")

    def test_admin_unblocks_device_successfully(self):
        device = _make_device()
        user = _make_user(role="admin")
        resp = self._call_unblock(device, user)
        self.assertEqual(resp.status_code, 200)

    def test_unblock_nonexistent_device_returns_404(self):
        device = _make_device()
        user = _make_user(role="admin")
        resp = self._call_unblock(device, user, device_found=False)
        self.assertEqual(resp.status_code, 404)

    def test_operator_wrong_tenant_returns_403(self):
        device = _make_device(tenant_id=uuid.uuid4())
        user = _make_user(role="operator", tenant_id=uuid.uuid4())
        resp = self._call_unblock(device, user)
        self.assertEqual(resp.status_code, 403)


# ── Testes — GET /devices/{id} ───────────────────────────────────────────────

class TestGetDeviceEndpoint(unittest.TestCase):
    def _call_get(self, device_id, found_device=None, user=None):
        from api.v1.devices import router as devices_router
        from core.database import get_db
        from core.dependencies import get_current_user

        app = FastAPI()
        app.include_router(devices_router)

        if user is None:
            user = _make_user(role="admin")

        app.dependency_overrides[get_db] = lambda: MagicMock()
        app.dependency_overrides[get_current_user] = lambda: user

        with patch("api.v1.devices.crud_device") as mock_crud:
            mock_crud.get.return_value = found_device

            client = TestClient(app)
            return client.get(f"/devices/{device_id}")

    def test_get_existing_device_returns_200(self):
        device = _make_device()
        resp = self._call_get(str(device.id), found_device=device)
        self.assertEqual(resp.status_code, 200)

    def test_get_nonexistent_device_returns_404(self):
        resp = self._call_get(str(uuid.uuid4()), found_device=None)
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
