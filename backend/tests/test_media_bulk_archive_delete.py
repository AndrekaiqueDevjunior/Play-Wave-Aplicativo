"""Testes SPEC 018 — selecao em massa (arquivar/excluir) de midias.

Mesmo padrao das SPECs 016/017, adaptado para Media: filtro de arquivadas
por padrao em GET /media, sincronizacao de archived_at no enum status, e
bloqueio de exclusao quando a midia esta em uso (CampaignPlaylistItem com
FK RESTRICT, ou os campos legados Campaign.media_ids/media_order) — tanto
no DELETE individual quanto no bulk-delete, que processa cada item
independentemente e nunca falha o lote inteiro por causa de um item.
"""
import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from api.v1.media import (
    bulk_archive_media,
    bulk_delete_media,
    delete_media,
    get_media,
)
from core.models import Media
from core.schemas_completos import MediaBulkActionRequest
from crud.entidades.crud_media import crud_media


def _make_media(**overrides):
    defaults = dict(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        name="Midia Teste",
        type="image",
        status="available",
        archived_at=None,
    )
    defaults.update(overrides)
    return Media(**defaults)


class TestMediaListingFilters(unittest.TestCase):
    def test_get_media_excludes_archived_by_default(self):
        admin = SimpleNamespace(role="admin", tenant_id=None)
        db = MagicMock()
        available = _make_media(status="available")
        archived = _make_media(status="archived")

        with patch(
            "api.v1.media.crud_media.get_multi",
            return_value=[available, archived],
        ):
            result = get_media(
                db=db,
                current_user=admin,
                skip=0,
                limit=100,
                search=None,
                media_type=None,
                status=None,
                category=None,
                tags=None,
                tenant_id=None,
                include_archived=False,
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, available.id)

    def test_get_media_include_archived_keeps_archived(self):
        admin = SimpleNamespace(role="admin", tenant_id=None)
        db = MagicMock()
        available = _make_media(status="available")
        archived = _make_media(status="archived")

        with patch(
            "api.v1.media.crud_media.get_multi",
            return_value=[available, archived],
        ):
            result = get_media(
                db=db,
                current_user=admin,
                skip=0,
                limit=100,
                search=None,
                media_type=None,
                status=None,
                category=None,
                tags=None,
                tenant_id=None,
                include_archived=True,
            )

        self.assertEqual(len(result), 2)


class TestMediaArchivedAtSync(unittest.TestCase):
    def test_update_status_helper_sets_archived_at(self):
        db = MagicMock()
        media = _make_media(status="available", archived_at=None)

        crud_media.update_status(db, db_obj=media, status="archived")
        self.assertIsNotNone(media.archived_at)

    def test_update_status_helper_clears_archived_at_on_restore(self):
        from datetime import datetime

        db = MagicMock()
        media = _make_media(status="archived", archived_at=datetime(2026, 6, 1))

        crud_media.update_status(db, db_obj=media, status="available")
        self.assertIsNone(media.archived_at)


class TestMediaSingleDeleteGuard(unittest.TestCase):
    def test_delete_blocked_when_in_campaign_playlist_item(self):
        media = _make_media()
        user = SimpleNamespace(role="admin", tenant_id=media.tenant_id)
        db = MagicMock()

        with patch("api.v1.media.crud_media.get", return_value=media), \
             patch(
                 "api.v1.media.crud_media.get_in_use_references",
                 return_value={"campaign_playlist_items": 2, "legacy_campaigns": 0, "in_use": True},
             ):
            with self.assertRaises(HTTPException) as ctx:
                delete_media(db=db, current_user=user, media_id=str(media.id), force=False)

        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("playlists de campanha", str(ctx.exception.detail))

    def test_delete_blocked_when_in_campaign_playlist_item_even_with_force(self):
        # force=True só desvincula os campos legados (Campaign.media_ids/
        # media_order); nunca remove CampaignPlaylistItem automaticamente.
        media = _make_media()
        user = SimpleNamespace(role="admin", tenant_id=media.tenant_id)
        db = MagicMock()

        with patch("api.v1.media.crud_media.get", return_value=media), \
             patch(
                 "api.v1.media.crud_media.get_in_use_references",
                 return_value={"campaign_playlist_items": 1, "legacy_campaigns": 0, "in_use": True},
             ):
            with self.assertRaises(HTTPException) as ctx:
                delete_media(db=db, current_user=user, media_id=str(media.id), force=True)

        self.assertEqual(ctx.exception.status_code, 409)

    def test_delete_allowed_when_not_in_use(self):
        media = _make_media()
        user = SimpleNamespace(role="admin", tenant_id=media.tenant_id)
        db = MagicMock()

        with patch("api.v1.media.crud_media.get", return_value=media), \
             patch(
                 "api.v1.media.crud_media.get_in_use_references",
                 return_value={"campaign_playlist_items": 0, "legacy_campaigns": 0, "in_use": False},
             ), \
             patch("api.v1.media._campaigns_using_media", return_value=[]), \
             patch("api.v1.media.crud_media.remove") as remove_mock, \
             patch("os.path.exists", return_value=False):
            result = delete_media(db=db, current_user=user, media_id=str(media.id), force=False)

        remove_mock.assert_called_once()
        self.assertIn("removida", result["message"])


class TestMediaBulkArchive(unittest.TestCase):
    def test_bulk_archive_processes_each_item_independently(self):
        media_a = _make_media()
        media_b = _make_media()
        user = SimpleNamespace(role="admin", tenant_id=media_a.tenant_id)
        db = MagicMock()
        payload = MediaBulkActionRequest(media_ids=[str(media_a.id), str(media_b.id)])

        def fake_get(_db, *, id):
            return {str(media_a.id): media_a, str(media_b.id): media_b}.get(id)

        with patch("api.v1.media.crud_media.get", side_effect=fake_get):
            result = bulk_archive_media(db=db, current_user=user, payload=payload)

        self.assertEqual(result.requested, 2)
        self.assertEqual(result.succeeded, 2)
        self.assertEqual(result.failed, 0)
        self.assertEqual(media_a.status, "archived")
        self.assertEqual(media_b.status, "archived")

    def test_bulk_archive_reports_failure_for_missing_media_without_failing_others(self):
        media_a = _make_media()
        missing_id = str(uuid.uuid4())
        user = SimpleNamespace(role="admin", tenant_id=media_a.tenant_id)
        db = MagicMock()
        payload = MediaBulkActionRequest(media_ids=[str(media_a.id), missing_id])

        def fake_get(_db, *, id):
            return media_a if id == str(media_a.id) else None

        with patch("api.v1.media.crud_media.get", side_effect=fake_get):
            result = bulk_archive_media(db=db, current_user=user, payload=payload)

        self.assertEqual(result.succeeded, 1)
        self.assertEqual(result.failed, 1)
        failed_result = next(r for r in result.results if not r.success)
        self.assertEqual(failed_result.media_id, missing_id)
        self.assertIn("não encontrada", failed_result.reason)


class TestMediaBulkDelete(unittest.TestCase):
    def test_bulk_delete_skips_media_in_use_reports_reason(self):
        media_free = _make_media()
        media_used = _make_media()
        user = SimpleNamespace(role="admin", tenant_id=media_free.tenant_id)
        db = MagicMock()
        payload = MediaBulkActionRequest(media_ids=[str(media_free.id), str(media_used.id)])

        def fake_get(_db, *, id):
            return {str(media_free.id): media_free, str(media_used.id): media_used}.get(id)

        def fake_refs(_db, *, media_id):
            if media_id == str(media_used.id):
                return {"campaign_playlist_items": 3, "legacy_campaigns": 0, "in_use": True}
            return {"campaign_playlist_items": 0, "legacy_campaigns": 0, "in_use": False}

        with patch("api.v1.media.crud_media.get", side_effect=fake_get), \
             patch("api.v1.media.crud_media.get_in_use_references", side_effect=fake_refs), \
             patch("api.v1.media._campaigns_using_media", return_value=[]), \
             patch("api.v1.media.crud_media.remove") as remove_mock, \
             patch("os.path.exists", return_value=False):
            result = bulk_delete_media(db=db, current_user=user, payload=payload)

        self.assertEqual(result.succeeded, 1)
        self.assertEqual(result.failed, 1)
        remove_mock.assert_called_once()
        failed_result = next(r for r in result.results if not r.success)
        self.assertEqual(failed_result.media_id, str(media_used.id))
        self.assertIn("playlist", failed_result.reason)

    def test_bulk_delete_reports_legacy_campaign_usage(self):
        media = _make_media()
        user = SimpleNamespace(role="admin", tenant_id=media.tenant_id)
        db = MagicMock()
        payload = MediaBulkActionRequest(media_ids=[str(media.id)])
        fake_campaign = SimpleNamespace(id=uuid.uuid4(), name="Campanha X")

        with patch("api.v1.media.crud_media.get", return_value=media), \
             patch(
                 "api.v1.media.crud_media.get_in_use_references",
                 return_value={"campaign_playlist_items": 0, "legacy_campaigns": 1, "in_use": True},
             ), \
             patch("api.v1.media._campaigns_using_media", return_value=[fake_campaign]):
            result = bulk_delete_media(db=db, current_user=user, payload=payload)

        self.assertEqual(result.failed, 1)
        self.assertIn("campanha", result.results[0].reason)

    def test_bulk_delete_all_succeed_when_none_in_use(self):
        media_a = _make_media()
        media_b = _make_media()
        user = SimpleNamespace(role="admin", tenant_id=media_a.tenant_id)
        db = MagicMock()
        payload = MediaBulkActionRequest(media_ids=[str(media_a.id), str(media_b.id)])

        def fake_get(_db, *, id):
            return {str(media_a.id): media_a, str(media_b.id): media_b}.get(id)

        with patch("api.v1.media.crud_media.get", side_effect=fake_get), \
             patch(
                 "api.v1.media.crud_media.get_in_use_references",
                 return_value={"campaign_playlist_items": 0, "legacy_campaigns": 0, "in_use": False},
             ), \
             patch("api.v1.media._campaigns_using_media", return_value=[]), \
             patch("api.v1.media.crud_media.remove") as remove_mock, \
             patch("os.path.exists", return_value=False):
            result = bulk_delete_media(db=db, current_user=user, payload=payload)

        self.assertEqual(result.requested, 2)
        self.assertEqual(result.succeeded, 2)
        self.assertEqual(result.failed, 0)
        self.assertEqual(remove_mock.call_count, 2)


class TestMediaInUseReferences(unittest.TestCase):
    def test_get_in_use_references_counts_playlist_items_and_legacy(self):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.count.return_value = 4
        query.all.return_value = []

        refs = crud_media.get_in_use_references(db, media_id="media-1")
        self.assertEqual(refs["campaign_playlist_items"], 4)
        self.assertTrue(refs["in_use"])

    def test_get_in_use_references_not_in_use_when_no_references(self):
        db = MagicMock()
        query = MagicMock()
        db.query.return_value = query
        query.filter.return_value = query
        query.count.return_value = 0
        query.all.return_value = []

        refs = crud_media.get_in_use_references(db, media_id="media-1")
        self.assertFalse(refs["in_use"])


if __name__ == "__main__":
    unittest.main()
