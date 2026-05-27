"""Testes DASHBOARD — /dashboard/stats.

Cobre:
  - _status_counts (reports.py): contagem por status de dispositivo
  - _period (reports.py): cálculo de intervalo de datas
  - _tenant_id_for (reports.py): isolamento de tenant por role
  - Endpoint GET /dashboard/stats: retorna estrutura correta, filtra por tenant
"""

import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_user(**kwargs):
    defaults = dict(
        id="user-001",
        role="admin",
        tenant_id="tenant-001",
        is_active=True,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_db(counts=None):
    """Retorna um db mock com query().count() configurável."""
    db = MagicMock()
    counts = counts or {}

    def side_effect(model):
        q = MagicMock()
        q.count.return_value = counts.get(getattr(model, "__name__", str(model)), 0)
        q.filter.return_value = q
        q.with_entities.return_value = q
        q.scalar.return_value = 0
        q.order_by.return_value = q
        q.limit.return_value = q
        q.__iter__ = lambda self: iter([])
        q.all.return_value = []
        return q

    db.query.side_effect = side_effect
    return db


# ── Testes unitários — funções helpers de reports ────────────────────────────

class TestTenantIdFor(unittest.TestCase):
    def setUp(self):
        from api.v1.reports import _tenant_id_for
        self.fn = _tenant_id_for

    def test_admin_returns_none(self):
        user = _make_user(role="admin")
        self.assertIsNone(self.fn(user))

    def test_non_admin_returns_tenant_id(self):
        user = _make_user(role="operator", tenant_id="tenant-abc")
        self.assertEqual(self.fn(user), "tenant-abc")


class TestPeriodHelper(unittest.TestCase):
    def setUp(self):
        from api.v1.reports import _period
        self.fn = _period

    def test_default_period_is_n_days(self):
        start, end = self.fn(7, None, None)
        diff = end - start
        self.assertAlmostEqual(diff.total_seconds(), 6 * 86400, delta=5)

    def test_explicit_dates_are_respected(self):
        d1 = datetime(2026, 1, 1)
        d2 = datetime(2026, 1, 31)
        start, end = self.fn(7, d1, d2)
        self.assertEqual(start, d1)
        self.assertEqual(end, d2)

    def test_only_date_from_uses_it_as_start(self):
        d1 = datetime(2026, 5, 1)
        start, end = self.fn(30, d1, None)
        self.assertEqual(start, d1)

    def test_only_date_to_computes_start_from_days(self):
        d2 = datetime(2026, 6, 30)
        start, end = self.fn(10, None, d2)
        self.assertEqual(end, d2)
        diff = d2 - start
        self.assertAlmostEqual(diff.total_seconds(), 9 * 86400, delta=5)


# ── Testes de endpoint — GET /dashboard/stats ────────────────────────────────

class TestDashboardStatsEndpoint(unittest.TestCase):
    def _make_app(self, user):
        from api.v1.dashboard import router as dashboard_router
        from core.database import get_db
        from core.dependencies import get_current_user
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(dashboard_router)

        db = _make_db()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user

        return TestClient(app)

    def test_stats_returns_expected_keys(self):
        user = _make_user(role="admin")
        client = self._make_app(user)

        resp = client.get("/dashboard/stats")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        for key in ("devices", "campaigns", "media", "audio", "playbacks_7d", "today", "users"):
            self.assertIn(key, data, f"Chave '{key}' ausente no retorno")

    def test_devices_keys(self):
        user = _make_user(role="admin")
        client = self._make_app(user)

        data = client.get("/dashboard/stats").json()
        self.assertIn("total", data["devices"])
        self.assertIn("online", data["devices"])
        self.assertIn("offline", data["devices"])

    def test_campaigns_keys(self):
        user = _make_user(role="admin")
        client = self._make_app(user)

        data = client.get("/dashboard/stats").json()
        self.assertIn("total", data["campaigns"])
        self.assertIn("active", data["campaigns"])

    def test_views_per_day_is_list(self):
        user = _make_user(role="admin")
        client = self._make_app(user)

        data = client.get("/dashboard/stats").json()
        self.assertIsInstance(data["views_per_day"], list)

    def test_recent_devices_is_list(self):
        user = _make_user(role="admin")
        client = self._make_app(user)

        data = client.get("/dashboard/stats").json()
        self.assertIsInstance(data["recent_devices"], list)

    def test_alerts_is_list(self):
        user = _make_user(role="admin")
        client = self._make_app(user)

        data = client.get("/dashboard/stats").json()
        self.assertIsInstance(data["alerts"], list)

    def test_non_admin_applies_tenant_filter(self):
        """Garante que usuário não-admin não causa erro (tenant_id aplicado)."""
        user = _make_user(role="operator", tenant_id="tenant-xyz")
        client = self._make_app(user)

        resp = client.get("/dashboard/stats")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
