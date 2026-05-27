"""Testes SPEC AUTH — Autenticação JWT.

Cobre:
  - create_access_token: geração de token com e sem expiração customizada
  - decode_access_token: decodificação válida, token expirado, token inválido
  - verify_password: senha correta, senha errada
  - Endpoint POST /api/auth/login: credenciais corretas, erradas, usuário inativo
  - Endpoint GET /api/auth/me: token válido, sem token, token inválido
  - Endpoint POST /api/auth/logout: sempre retorna sucesso
"""

import unittest
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_user(**kwargs):
    defaults = dict(
        id=uuid.uuid4(),
        email="admin@playwave.com",
        password_hash="hashed-secret",
        role="admin",
        tenant_id=uuid.uuid4(),
        is_active=True,
        name="Admin",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── Testes unitários — create_access_token / decode_access_token ─────────────

class TestJWTFunctions(unittest.TestCase):
    def test_token_round_trip(self):
        from core.auth import create_access_token, decode_access_token

        token = create_access_token({"sub": "user-123"})
        payload = decode_access_token(token)

        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "user-123")

    def test_decode_invalid_token_returns_none(self):
        from core.auth import decode_access_token

        result = decode_access_token("este.token.invalido")
        self.assertIsNone(result)

    def test_decode_expired_token_returns_none(self):
        from core.auth import create_access_token, decode_access_token

        token = create_access_token({"sub": "x"}, expires_delta=timedelta(seconds=-1))
        result = decode_access_token(token)
        self.assertIsNone(result)

    def test_custom_expiry_is_set(self):
        from core.auth import create_access_token, decode_access_token

        token = create_access_token({"sub": "y"}, expires_delta=timedelta(hours=1))
        payload = decode_access_token(token)
        self.assertIn("exp", payload)


# ── Testes unitários — verify_password ───────────────────────────────────────

class TestVerifyPassword(unittest.TestCase):
    def setUp(self):
        from core.auth import get_password_hash
        self.hash = get_password_hash("senha123")

    def test_correct_password_returns_true(self):
        from core.auth import verify_password
        self.assertTrue(verify_password("senha123", self.hash))

    def test_wrong_password_returns_false(self):
        from core.auth import verify_password
        self.assertFalse(verify_password("errada", self.hash))

    def test_empty_password_returns_false(self):
        from core.auth import verify_password
        self.assertFalse(verify_password("", self.hash))


# ── Testes de endpoint — /api/auth/login ─────────────────────────────────────

@contextmanager
def _make_auth_app(user_in_db=None, *, verify_ok=True):
    """Monta app mínima com o router de auth injetando mocks."""
    from api.v1.auth import router as auth_router
    from core.database import get_db

    app = FastAPI()
    app.include_router(auth_router)

    fake_db = MagicMock()
    query_mock = MagicMock()
    query_mock.filter.return_value.first.return_value = user_in_db
    fake_db.query.return_value = query_mock

    app.dependency_overrides[get_db] = lambda: fake_db

    with patch("api.v1.auth.verify_password", return_value=verify_ok):
        with patch(
            "api.v1.auth.create_access_token",
            return_value="fake-jwt-token",
        ):
            yield TestClient(app)


class TestLoginEndpoint(unittest.TestCase):
    def test_valid_credentials_return_token(self):
        user = _make_user()
        with _make_auth_app(user_in_db=user, verify_ok=True) as client:
            resp = client.post(
                "/api/auth/login",
                json={"email": "admin@playwave.com", "password": "senha123"},
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")

    def test_wrong_password_returns_401(self):
        user = _make_user()
        with _make_auth_app(user_in_db=user, verify_ok=False) as client:
            resp = client.post(
                "/api/auth/login",
                json={"email": "admin@playwave.com", "password": "errada"},
            )
        self.assertEqual(resp.status_code, 401)

    def test_unknown_email_returns_401(self):
        with _make_auth_app(user_in_db=None, verify_ok=False) as client:
            resp = client.post(
                "/api/auth/login",
                json={"email": "nao@existe.com", "password": "qualquer"},
            )
        self.assertEqual(resp.status_code, 401)

    def test_inactive_user_returns_403(self):
        user = _make_user(is_active=False)
        with _make_auth_app(user_in_db=user, verify_ok=True) as client:
            resp = client.post(
                "/api/auth/login",
                json={"email": "admin@playwave.com", "password": "senha123"},
            )
        self.assertEqual(resp.status_code, 403)

    def test_missing_fields_returns_422(self):
        with _make_auth_app(user_in_db=None) as client:
            resp = client.post("/api/auth/login", json={})
        self.assertEqual(resp.status_code, 422)


# ── Testes de endpoint — /api/auth/me ────────────────────────────────────────

class TestMeEndpoint(unittest.TestCase):
    def _app(self, current_user=None, raise_401=False):
        from api.v1.auth import router as auth_router
        from core.dependencies import get_current_user
        from fastapi import HTTPException

        app = FastAPI()
        app.include_router(auth_router)

        if raise_401:
            def fake_get_user():
                raise HTTPException(status_code=401, detail="Não autenticado")
            app.dependency_overrides[get_current_user] = fake_get_user
        else:
            app.dependency_overrides[get_current_user] = lambda: current_user

        return TestClient(app)

    def test_me_returns_current_user(self):
        user = _make_user()
        client = self._app(current_user=user)
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer fake-token"})
        self.assertEqual(resp.status_code, 200)

    def test_me_without_token_returns_401(self):
        client = self._app(raise_401=True)
        resp = client.get("/api/auth/me")
        self.assertEqual(resp.status_code, 401)


# ── Testes de endpoint — /api/auth/logout ────────────────────────────────────

class TestLogoutEndpoint(unittest.TestCase):
    def test_logout_always_succeeds(self):
        from api.v1.auth import router as auth_router

        app = FastAPI()
        app.include_router(auth_router)
        client = TestClient(app)

        resp = client.post("/api/auth/logout")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("message", resp.json())


if __name__ == "__main__":
    unittest.main()
