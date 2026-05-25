"""Testes SPEC 004 — Pareamento e Revogação.

Cobre:
  - DeviceAuthError: serialização correta do error_code
  - get_device_by_token: TOKEN_VERSION_MISMATCH, TOKEN_REVOKED, REQUIRES_REPAIRING,
    compat sem header
  - Endpoint POST /devices/{id}/force-repair: não altera pairing_code, incrementa
    token_version, registra evento
  - Endpoint POST /devices/{id}/pairing-code/regenerate: registra evento
    code_regenerated, altera pairing_code
  - Endpoint GET /devices/{id}/pairing-events: lista e filtra por event_type
"""

import uuid
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call

from fastapi import FastAPI
from fastapi.testclient import TestClient

# ── helpers ──────────────────────────────────────────────────────────────────

def _make_device(**kwargs):
    """Cria um SimpleNamespace imitando um Device do SQLAlchemy."""
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        pairing_code="TV-ABCD",
        device_token="tok-valid",
        is_blocked=False,
        requires_repairing=False,
        token_version=3,
        pairing_version=1,
        status="online",
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


# ── Unit tests — DeviceAuthError ─────────────────────────────────────────────

class TestDeviceAuthError(unittest.TestCase):
    def setUp(self):
        from api.v1.devices import DeviceAuthError
        self.DeviceAuthError = DeviceAuthError

    def test_error_code_stored(self):
        err = self.DeviceAuthError(error_code="TOKEN_REVOKED", detail="revoked")
        self.assertEqual(err.error_code, "TOKEN_REVOKED")

    def test_default_status_is_401(self):
        err = self.DeviceAuthError(error_code="TOKEN_REVOKED", detail="revoked")
        self.assertEqual(err.status_code, 401)

    def test_custom_status(self):
        err = self.DeviceAuthError(
            error_code="DEVICE_BLOCKED", detail="blocked", status_code=403
        )
        self.assertEqual(err.status_code, 403)

    def test_detail_payload_includes_error_code(self):
        err = self.DeviceAuthError(error_code="TOKEN_VERSION_MISMATCH", detail="mismatch",
                                   current_version=5, received_version=3)
        self.assertIsInstance(err.detail, dict)
        self.assertEqual(err.detail["error_code"], "TOKEN_VERSION_MISMATCH")
        self.assertEqual(err.detail["current_version"], 5)
        self.assertEqual(err.detail["received_version"], 3)


# ── Unit tests — get_device_by_token ─────────────────────────────────────────

class TestGetDeviceByToken(unittest.TestCase):
    def setUp(self):
        from api.v1.devices import get_device_by_token, DeviceAuthError
        self.get_device_by_token = get_device_by_token
        self.DeviceAuthError = DeviceAuthError

    def _call(self, device, token_version_header=None):
        """Chama get_device_by_token com crud_device mockado."""
        db = MagicMock()
        with patch("api.v1.devices.crud_device") as mock_crud:
            mock_crud.get_by_device_token.return_value = device
            return self.get_device_by_token(
                x_device_token="tok-valid",
                x_device_token_version=token_version_header,
                db=db,
            )

    def test_valid_token_and_version_passes(self):
        device = _make_device(token_version=3)
        result = self._call(device, token_version_header="3")
        self.assertIs(result, device)

    def test_missing_header_compat_passes(self):
        device = _make_device(token_version=3)
        result = self._call(device, token_version_header=None)
        self.assertIs(result, device)

    def test_wrong_version_raises_mismatch(self):
        device = _make_device(token_version=5)
        with self.assertRaises(self.DeviceAuthError) as ctx:
            self._call(device, token_version_header="3")
        self.assertEqual(ctx.exception.error_code, "TOKEN_VERSION_MISMATCH")
        self.assertEqual(ctx.exception.detail["current_version"], 5)
        self.assertEqual(ctx.exception.detail["received_version"], 3)

    def test_revoked_token_raises_token_revoked(self):
        db = MagicMock()
        with patch("api.v1.devices.crud_device") as mock_crud:
            mock_crud.get_by_device_token.return_value = None
            with self.assertRaises(self.DeviceAuthError) as ctx:
                self.get_device_by_token(
                    x_device_token="tok-bad",
                    x_device_token_version="1",
                    db=db,
                )
        self.assertEqual(ctx.exception.error_code, "TOKEN_REVOKED")

    def test_requires_repairing_raises(self):
        device = _make_device(requires_repairing=True)
        with self.assertRaises(self.DeviceAuthError) as ctx:
            self._call(device, token_version_header="3")
        self.assertEqual(ctx.exception.error_code, "REQUIRES_REPAIRING")

    def test_blocked_device_raises(self):
        device = _make_device(is_blocked=True)
        with self.assertRaises(self.DeviceAuthError) as ctx:
            self._call(device, token_version_header="3")
        self.assertEqual(ctx.exception.error_code, "DEVICE_BLOCKED")
        self.assertEqual(ctx.exception.status_code, 403)

    def test_invalid_version_header_format_raises(self):
        device = _make_device(token_version=3)
        with self.assertRaises(self.DeviceAuthError) as ctx:
            self._call(device, token_version_header="abc")
        self.assertEqual(ctx.exception.error_code, "TOKEN_VERSION_REQUIRED")


# ── Endpoint tests via TestClient ─────────────────────────────────────────────

def _build_test_app():
    """Monta um FastAPI mínimo com o router de devices."""
    from main import app
    return app


class TestForceRepairEndpoint(unittest.TestCase):
    """POST /devices/{id}/force-repair — SPEC 004."""

    def setUp(self):
        self.device = _make_device(
            id=uuid.uuid4(),
            pairing_code="TV-ORIG",
            device_token="tok-valid",
            token_version=2,
            pairing_version=1,
        )
        self.admin = _make_user(role="admin", tenant_id=self.device.tenant_id)
        self.device_id = str(self.device.id)

    def _client(self, mock_db):
        from main import app
        from core.dependencies import get_current_user
        from core.database import get_db

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: self.admin
        client = TestClient(app, raise_server_exceptions=True)
        return client

    def tearDown(self):
        from main import app
        app.dependency_overrides.clear()

    def test_pairing_code_unchanged_after_force_repair(self):
        mock_db = MagicMock()

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_pairing_event") as mock_event, \
             patch("api.v1.devices._revoke_device_sessions", return_value=1), \
             patch("api.v1.devices._invalidate_device_playlist_cache"), \
             patch("api.v1.devices._publish_pairing_revoked"):

            mock_crud.get.return_value = self.device
            mock_event.log.return_value = MagicMock()

            client = self._client(mock_db)
            resp = client.post(
                f"/devices/{self.device_id}/force-repair",
                json={"reason": "player suspeito"},
            )

        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        # pairing_code não muda
        self.assertEqual(data["pairing_code_unchanged"], "TV-ORIG")
        # token_version incrementa
        self.assertEqual(data["token_version"], 3)

    def test_force_repair_logs_event(self):
        mock_db = MagicMock()

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_pairing_event") as mock_event, \
             patch("api.v1.devices._revoke_device_sessions", return_value=0), \
             patch("api.v1.devices._invalidate_device_playlist_cache"), \
             patch("api.v1.devices._publish_pairing_revoked"):

            mock_crud.get.return_value = self.device
            mock_event.log.return_value = MagicMock()

            client = self._client(mock_db)
            client.post(
                f"/devices/{self.device_id}/force-repair",
                json={"reason": "teste"},
            )

        mock_event.log.assert_called_once()
        call_kwargs = mock_event.log.call_args.kwargs
        self.assertEqual(call_kwargs["event_type"], "force_repair")
        self.assertEqual(call_kwargs["previous_token_version"], 2)
        self.assertEqual(call_kwargs["new_token_version"], 3)

    def test_force_repair_sets_requires_repairing(self):
        mock_db = MagicMock()

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_pairing_event"), \
             patch("api.v1.devices._revoke_device_sessions", return_value=0), \
             patch("api.v1.devices._invalidate_device_playlist_cache"), \
             patch("api.v1.devices._publish_pairing_revoked"):

            mock_crud.get.return_value = self.device
            client = self._client(mock_db)
            client.post(f"/devices/{self.device_id}/force-repair")

        self.assertTrue(self.device.requires_repairing)
        self.assertIsNone(self.device.device_token)

    def test_force_repair_device_not_found_returns_404(self):
        mock_db = MagicMock()

        with patch("api.v1.devices.crud_device") as mock_crud:
            mock_crud.get.return_value = None
            client = self._client(mock_db)
            resp = client.post(f"/devices/{uuid.uuid4()}/force-repair")

        self.assertEqual(resp.status_code, 404)


class TestRegenerateEndpoint(unittest.TestCase):
    """POST /devices/{id}/pairing-code/regenerate — SPEC 004.

    Testa a função do endpoint diretamente (sem TestClient) para evitar
    problemas de threading com os mocks do unittest.mock.patch.
    """

    def setUp(self):
        self.device = _make_device(
            id=uuid.uuid4(),
            pairing_code="TV-OLD",
            device_token="tok-valid",
            token_version=1,
            pairing_version=1,
        )
        self.admin = _make_user(role="admin", tenant_id=self.device.tenant_id)

    def _call_regenerate(self, reason=None, mock_revoked=0):
        """Chama a função de regenerar código diretamente, com todos os CRUDs mockados."""
        from api.v1.devices import regenerate_pairing_code
        from core.schemas_completos import RegenerateCodeRequest

        mock_db = MagicMock()
        body = RegenerateCodeRequest(reason=reason) if reason else None

        mock_crud_device = MagicMock()
        mock_crud_device.get.return_value = self.device
        mock_crud_device.get_by_pairing_code.return_value = None  # candidato livre

        mock_crud_event = MagicMock()
        mock_crud_pairing_code = MagicMock()
        mock_crud_pairing_code.get_by_pairing_code.return_value = None  # código livre

        with patch("api.v1.devices.crud_device", mock_crud_device), \
             patch("api.v1.devices.crud_device_pairing_event", mock_crud_event), \
             patch("api.v1.devices.crud_device_pairing_code", mock_crud_pairing_code), \
             patch("api.v1.devices._revoke_device_sessions", return_value=mock_revoked), \
             patch("api.v1.devices._invalidate_device_playlist_cache"), \
             patch("api.v1.devices._publish_pairing_revoked"):

            result = regenerate_pairing_code(
                db=mock_db,
                current_user=self.admin,
                device_id=str(self.device.id),
                body=body,
            )

        return result, mock_crud_event

    def test_regenerate_logs_code_regenerated_event(self):
        result, mock_crud_event = self._call_regenerate(
            reason="Suspeita de crachá clonado", mock_revoked=1
        )

        self.assertEqual(result.previous_pairing_code, "TV-OLD")

        mock_crud_event.log.assert_called_once()
        call_kwargs = mock_crud_event.log.call_args.kwargs
        self.assertEqual(call_kwargs["event_type"], "code_regenerated")
        self.assertEqual(call_kwargs["reason"], "Suspeita de crachá clonado")
        self.assertEqual(call_kwargs["previous_pairing_code"], "TV-OLD")

    def test_regenerate_increments_both_versions(self):
        result, _ = self._call_regenerate()

        self.assertEqual(result.pairing_version, 2)
        self.assertEqual(result.token_version, 2)

    def test_regenerate_revoked_sessions_count_in_response(self):
        result, _ = self._call_regenerate(mock_revoked=3)

        self.assertEqual(result.revoked_sessions_count, 3)

    def test_regenerate_changes_pairing_code(self):
        result, _ = self._call_regenerate()

        # O novo código não deve ser o mesmo que o antigo
        self.assertNotEqual(result.pairing_code, "TV-OLD")


class TestPairingEventsEndpoint(unittest.TestCase):
    """GET /devices/{id}/pairing-events — SPEC 004."""

    def setUp(self):
        self.device = _make_device(id=uuid.uuid4())
        self.admin = _make_user(role="admin", tenant_id=self.device.tenant_id)
        self.device_id = str(self.device.id)

    def _client(self, mock_db):
        from main import app
        from core.dependencies import get_current_user
        from core.database import get_db

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: self.admin
        return TestClient(app, raise_server_exceptions=True)

    def tearDown(self):
        from main import app
        app.dependency_overrides.clear()

    def _make_event(self, event_type="force_repair"):
        return SimpleNamespace(
            id=uuid.uuid4(),
            event_type=event_type,
            previous_token_version=1,
            new_token_version=2,
            previous_pairing_version=None,
            new_pairing_version=None,
            previous_pairing_code=None,
            new_pairing_code=None,
            requested_by=None,
            reason="teste",
            extra_metadata=None,
            created_at=datetime.utcnow(),
        )

    def test_returns_list_of_events(self):
        mock_db = MagicMock()
        events = [self._make_event("code_regenerated"), self._make_event("force_repair")]

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_pairing_event") as mock_event:

            mock_crud.get.return_value = self.device
            mock_event.list_by_device.return_value = events
            mock_event.count_by_device.return_value = 2
            mock_db.query.return_value.filter.return_value.first.return_value = None

            client = self._client(mock_db)
            resp = client.get(f"/devices/{self.device_id}/pairing-events")

        self.assertEqual(resp.status_code, 200, resp.text)
        data = resp.json()
        self.assertEqual(data["total"], 2)
        self.assertEqual(len(data["items"]), 2)
        self.assertEqual(data["items"][0]["event_type"], "code_regenerated")

    def test_filters_by_event_type(self):
        mock_db = MagicMock()
        events = [self._make_event("force_repair")]

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_pairing_event") as mock_event:

            mock_crud.get.return_value = self.device
            mock_event.list_by_device.return_value = events
            mock_event.count_by_device.return_value = 1
            mock_db.query.return_value.filter.return_value.first.return_value = None

            client = self._client(mock_db)
            resp = client.get(
                f"/devices/{self.device_id}/pairing-events?event_type=force_repair"
            )

        self.assertEqual(resp.status_code, 200)
        mock_event.list_by_device.assert_called_once()
        call_kwargs = mock_event.list_by_device.call_args.kwargs
        self.assertEqual(call_kwargs["event_type"], "force_repair")

    def test_device_not_found_returns_404(self):
        mock_db = MagicMock()

        with patch("api.v1.devices.crud_device") as mock_crud:
            mock_crud.get.return_value = None
            client = self._client(mock_db)
            resp = client.get(f"/devices/{uuid.uuid4()}/pairing-events")

        self.assertEqual(resp.status_code, 404)

    def test_respects_limit_param(self):
        mock_db = MagicMock()

        with patch("api.v1.devices.crud_device") as mock_crud, \
             patch("api.v1.devices.crud_device_pairing_event") as mock_event:

            mock_crud.get.return_value = self.device
            mock_event.list_by_device.return_value = []
            mock_event.count_by_device.return_value = 0

            client = self._client(mock_db)
            resp = client.get(f"/devices/{self.device_id}/pairing-events?limit=10")

        self.assertEqual(resp.status_code, 200)
        call_kwargs = mock_event.list_by_device.call_args.kwargs
        self.assertEqual(call_kwargs["limit"], 10)


if __name__ == "__main__":
    unittest.main()
