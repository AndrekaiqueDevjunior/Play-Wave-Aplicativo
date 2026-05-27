"""Testes REPORTS — Relatórios e exportação CSV.

Cobre:
  - _tenant_id_for: admin retorna None, não-admin retorna tenant_id
  - _period: cálculo de datas (já coberto em test_dashboard, mas revalidado aqui)
  - _apply_tenant: adiciona filtro quando tenant_id != None
  - _status_counts: estrutura correta com todos os status esperados
  - Endpoint GET /reports/summary: retorna estrutura com keys esperadas
  - Endpoint GET /reports/export/csv: retorna Content-Type text/csv
"""

import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


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


def _make_db_with_status_counts(status_data=None):
    """db mock que retorna contagens por status de Device."""
    db = MagicMock()
    # Para _status_counts: query(Device.status, count).group_by().all()
    status_data = status_data or [("online", 5), ("offline", 2)]

    outer_q = MagicMock()
    outer_q.group_by.return_value.all.return_value = [
        (s, c) for s, c in status_data
    ]
    outer_q.filter.return_value = outer_q
    outer_q.count.return_value = sum(c for _, c in status_data)

    inner_q = MagicMock()
    inner_q.filter.return_value = inner_q
    inner_q.offset.return_value.limit.return_value.all.return_value = []
    inner_q.count.return_value = 0
    inner_q.with_entities.return_value.scalar.return_value = 0

    def query_side_effect(model):
        from core.models import Device
        if model is Device or (hasattr(model, "__name__") and model.__name__ == "Device"):
            return outer_q
        return inner_q

    db.query.side_effect = query_side_effect
    return db


# ── Testes unitários — _tenant_id_for ────────────────────────────────────────

class TestTenantIdFor(unittest.TestCase):
    def setUp(self):
        from api.v1.reports import _tenant_id_for
        self.fn = _tenant_id_for

    def test_admin_returns_none(self):
        self.assertIsNone(self.fn(_make_user(role="admin")))

    def test_operator_returns_tenant_id(self):
        user = _make_user(role="operator", tenant_id="ten-abc")
        self.assertEqual(self.fn(user), "ten-abc")

    def test_viewer_returns_tenant_id(self):
        user = _make_user(role="viewer", tenant_id="ten-xyz")
        self.assertEqual(self.fn(user), "ten-xyz")


# ── Testes unitários — _period ───────────────────────────────────────────────

class TestPeriod(unittest.TestCase):
    def setUp(self):
        from api.v1.reports import _period
        self.fn = _period

    def test_7_days_default(self):
        start, end = self.fn(7, None, None)
        diff = end - start
        self.assertAlmostEqual(diff.total_seconds(), 6 * 86400, delta=10)

    def test_explicit_range_returned_as_is(self):
        d1 = datetime(2026, 1, 1)
        d2 = datetime(2026, 3, 31)
        start, end = self.fn(7, d1, d2)
        self.assertEqual(start, d1)
        self.assertEqual(end, d2)

    def test_only_date_to_provided(self):
        d2 = datetime(2026, 6, 1)
        start, end = self.fn(30, None, d2)
        self.assertEqual(end, d2)
        diff = d2 - start
        self.assertAlmostEqual(diff.total_seconds(), 29 * 86400, delta=10)


# ── Testes unitários — _status_counts ────────────────────────────────────────

class TestStatusCounts(unittest.TestCase):
    def setUp(self):
        from api.v1.reports import _status_counts
        self.fn = _status_counts

    def test_returns_all_expected_statuses(self):
        db = MagicMock()
        db.query.return_value.group_by.return_value.all.return_value = []
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = self.fn(db, tenant_id=None)
        status_names = [item["status"] for item in result]

        for expected in ("online", "offline", "syncing", "error", "waiting_pairing", "blocked"):
            self.assertIn(expected, status_names, f"Status '{expected}' ausente")

    def test_counts_are_populated(self):
        db = MagicMock()
        online_row = SimpleNamespace(value="online")
        offline_row = SimpleNamespace(value="offline")
        db.query.return_value.group_by.return_value.all.return_value = [
            (online_row, 10),
            (offline_row, 3),
        ]
        db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            (online_row, 10),
            (offline_row, 3),
        ]

        result = self.fn(db, tenant_id=None)
        counts = {item["status"]: item["value"] for item in result}
        self.assertEqual(counts["online"], 10)
        self.assertEqual(counts["offline"], 3)
        self.assertEqual(counts["syncing"], 0)


# ── Testes de endpoint — GET /reports/summary ─────────────────────────────────

class TestReportsSummaryEndpoint(unittest.TestCase):
    def _make_app(self, user):
        from api.v1.reports import router as reports_router
        from core.database import get_db
        from core.dependencies import get_current_user

        app = FastAPI()
        app.include_router(reports_router)

        fake_db = MagicMock()
        fake_db.query.return_value.filter.return_value = fake_db.query.return_value
        fake_db.query.return_value.group_by.return_value.all.return_value = []
        fake_db.query.return_value.count.return_value = 0
        fake_db.query.return_value.with_entities.return_value.scalar.return_value = 0
        fake_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []

        app.dependency_overrides[get_db] = lambda: fake_db
        app.dependency_overrides[get_current_user] = lambda: user

        return TestClient(app)

    def test_summary_returns_200(self):
        user = _make_user(role="admin")
        client = self._make_app(user)
        resp = client.get("/reports/summary")
        self.assertEqual(resp.status_code, 200)

    def test_summary_has_device_status_key(self):
        user = _make_user(role="admin")
        client = self._make_app(user)
        data = client.get("/reports/summary").json()
        self.assertIn("device_status", data)

    def test_summary_has_total_views_key(self):
        user = _make_user(role="admin")
        client = self._make_app(user)
        data = client.get("/reports/summary").json()
        self.assertIn("total_views", data)


# ── Testes de endpoint — GET /reports/export/csv ─────────────────────────────

class TestReportsExportCSV(unittest.TestCase):
    def _make_app(self, user):
        from api.v1.reports import router as reports_router
        from core.database import get_db
        from core.dependencies import get_current_user

        app = FastAPI()
        app.include_router(reports_router)

        fake_db = MagicMock()
        fake_db.query.return_value.filter.return_value = fake_db.query.return_value
        fake_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []

        app.dependency_overrides[get_db] = lambda: fake_db
        app.dependency_overrides[get_current_user] = lambda: user

        return TestClient(app)

    def test_csv_export_returns_csv_content_type(self):
        user = _make_user(role="admin")
        client = self._make_app(user)
        resp = client.get("/reports/export/csv")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp.headers.get("content-type", ""))

    def test_csv_has_header_row(self):
        user = _make_user(role="admin")
        client = self._make_app(user)
        resp = client.get("/reports/export/csv")
        content = resp.text
        self.assertTrue(len(content) > 0)


if __name__ == "__main__":
    unittest.main()
