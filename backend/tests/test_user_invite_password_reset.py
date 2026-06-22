"""Testes SPEC 019 — convite por e-mail, reenvio, aceite e reset de senha.

Cobre: criação de usuário com convite (sem senha) vs. senha manual, bloqueio
de login para pending_invite/sem password_hash, reenvio de convite, aceite
de convite (token válido/expirado/inválido), forgot/reset de senha.
"""
import unittest
import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from api.v1.auth import login, accept_invite, forgot_password, reset_password
from api.v1.users import create_user, resend_invite
from core.models import User
from core.schemas import UserLogin
from core.schemas_completos import (
    UserCreate, UserAcceptInviteRequest, PasswordForgotRequest, PasswordResetConfirmRequest,
)


def _make_user(**overrides):
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Usuário Teste",
        email="teste@playwave.com",
        password_hash="hashed",
        role="operator",
        is_active=True,
        account_status="active",
        invite_token=None,
        invite_expires_at=None,
        password_reset_token=None,
        password_reset_expires_at=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    defaults.update(overrides)
    return User(**defaults)


class TestCreateUserInviteVsPassword(unittest.TestCase):
    def _make_db(self, email_exists=False):
        db = MagicMock()
        with patch("api.v1.users.crud_user.email_exists", return_value=email_exists):
            pass
        return db

    @patch("api.v1.users.crud_user.email_exists", return_value=False)
    @patch("api.v1.users.send_invite_email")
    @patch("api.v1.users.generate_secure_token", return_value="tok123")
    def test_create_user_with_invite_has_no_password_and_pending_status(
        self, mock_token, mock_send_email, mock_email_exists
    ):
        admin = SimpleNamespace(role="admin", tenant_id=None, email="admin@playwave.com")
        db = MagicMock()
        captured = {}

        def fake_add(obj):
            if isinstance(obj, User):
                captured["user"] = obj

        db.add.side_effect = fake_add
        db.refresh.side_effect = lambda obj: None

        payload = UserCreate(
            name="Novo Usuário",
            email="novo@playwave.com",
            role="operator",
            send_invite=True,
        )

        create_user(db=db, current_user=admin, user_in=payload)

        created = captured["user"]
        self.assertIsNone(created.password_hash)
        self.assertEqual(created.account_status, "pending_invite")
        self.assertEqual(created.invite_token, "tok123")
        mock_send_email.assert_called_once()

    @patch("api.v1.users.crud_user.email_exists", return_value=False)
    def test_create_user_with_manual_password_is_active_immediately(self, mock_email_exists):
        admin = SimpleNamespace(role="admin", tenant_id=None, email="admin@playwave.com")
        db = MagicMock()
        captured = {}

        def fake_add(obj):
            if isinstance(obj, User):
                captured["user"] = obj

        db.add.side_effect = fake_add
        db.refresh.side_effect = lambda obj: None

        payload = UserCreate(
            name="Novo Usuário",
            email="novo2@playwave.com",
            role="operator",
            send_invite=False,
            password="senha123",
        )

        create_user(db=db, current_user=admin, user_in=payload)

        created = captured["user"]
        self.assertIsNotNone(created.password_hash)
        self.assertEqual(created.account_status, "active")

    def test_create_user_requires_password_or_invite(self):
        with self.assertRaises(Exception):
            UserCreate(name="X", email="x@playwave.com", role="operator", send_invite=False)


class TestLoginBlocksPendingInviteAndNullPassword(unittest.TestCase):
    def test_login_rejects_user_without_password_hash_cleanly(self):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.first.return_value = _make_user(password_hash=None, account_status="pending_invite")

        with self.assertRaises(HTTPException) as ctx:
            login(UserLogin(email="teste@playwave.com", password="qualquer"), db=db)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_login_rejects_pending_invite_with_specific_message(self):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        user = _make_user(password_hash="hashed", account_status="pending_invite")
        query.first.return_value = user

        with self.assertRaises(HTTPException) as ctx:
            login(UserLogin(email="teste@playwave.com", password="qualquer"), db=db)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("Convite pendente", ctx.exception.detail)

    @patch("api.v1.auth.verify_password", return_value=True)
    def test_login_succeeds_for_active_user_with_password(self, mock_verify):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        user = _make_user()
        query.first.return_value = user

        token = login(UserLogin(email="teste@playwave.com", password="senha123"), db=db)
        self.assertIsNotNone(token.access_token)


class TestResendInvite(unittest.TestCase):
    def test_resend_invite_rejected_when_not_pending(self):
        admin = SimpleNamespace(role="admin", tenant_id=None, email="admin@playwave.com")
        db = MagicMock()
        user = _make_user(account_status="active")

        with patch("api.v1.users.crud_user.get", return_value=user):
            with self.assertRaises(HTTPException) as ctx:
                resend_invite(db=db, current_user=admin, user_id=str(user.id))
            self.assertEqual(ctx.exception.status_code, 400)

    @patch("api.v1.users.send_invite_email")
    @patch("api.v1.users.generate_secure_token", return_value="newtok")
    def test_resend_invite_generates_new_token_for_pending_user(self, mock_token, mock_send):
        admin = SimpleNamespace(role="admin", tenant_id=None, email="admin@playwave.com")
        db = MagicMock()
        user = _make_user(account_status="pending_invite", invite_token="oldtok")

        def fake_update(db, *, db_obj, obj_in):
            for k, v in obj_in.items():
                setattr(db_obj, k, v)
            return db_obj

        with patch("api.v1.users.crud_user.get", return_value=user), \
             patch("api.v1.users.crud_user.update", side_effect=fake_update):
            result = resend_invite(db=db, current_user=admin, user_id=str(user.id))

        self.assertEqual(user.invite_token, "newtok")
        mock_send.assert_called_once()
        self.assertIsNotNone(result.invite_sent_at)


class TestAcceptInvite(unittest.TestCase):
    def test_accept_invite_rejects_invalid_token(self):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.first.return_value = None

        with self.assertRaises(HTTPException) as ctx:
            accept_invite(UserAcceptInviteRequest(token="bad", password="senha123"), db=db)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_accept_invite_rejects_expired_token(self):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        user = _make_user(
            password_hash=None,
            account_status="pending_invite",
            invite_token="tok",
            invite_expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        query.first.return_value = user

        with self.assertRaises(HTTPException) as ctx:
            accept_invite(UserAcceptInviteRequest(token="tok", password="senha123"), db=db)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_accept_invite_with_valid_token_activates_user(self):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        user = _make_user(
            password_hash=None,
            account_status="pending_invite",
            invite_token="tok",
            invite_expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        query.first.return_value = user
        db.refresh.side_effect = lambda obj: None

        token = accept_invite(UserAcceptInviteRequest(token="tok", password="senha123"), db=db)

        self.assertEqual(user.account_status, "active")
        self.assertIsNone(user.invite_token)
        self.assertIsNotNone(user.password_hash)
        self.assertIsNotNone(token.access_token)


class TestForgotAndResetPassword(unittest.TestCase):
    def test_forgot_password_always_returns_generic_message_when_user_missing(self):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.first.return_value = None

        result = forgot_password(PasswordForgotRequest(email="ninguem@playwave.com"), db=db)
        self.assertIn("Se o e-mail existir", result["message"])

    @patch("api.v1.auth.send_password_reset_email")
    @patch("api.v1.auth.generate_secure_token", return_value="resettok")
    def test_forgot_password_generates_token_when_user_exists_with_password(
        self, mock_token, mock_send
    ):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        user = _make_user()
        query.first.return_value = user

        forgot_password(PasswordForgotRequest(email=user.email), db=db)

        self.assertEqual(user.password_reset_token, "resettok")
        mock_send.assert_called_once()

    def test_reset_password_rejects_expired_token(self):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        user = _make_user(
            password_reset_token="tok",
            password_reset_expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        query.first.return_value = user

        with self.assertRaises(HTTPException) as ctx:
            reset_password(PasswordResetConfirmRequest(token="tok", password="novaSenha1"), db=db)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_reset_password_with_valid_token_updates_password(self):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        user = _make_user(
            password_reset_token="tok",
            password_reset_expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        query.first.return_value = user
        db.refresh.side_effect = lambda obj: None

        token = reset_password(PasswordResetConfirmRequest(token="tok", password="novaSenha1"), db=db)

        self.assertIsNone(user.password_reset_token)
        self.assertIsNotNone(token.access_token)


if __name__ == "__main__":
    unittest.main()
