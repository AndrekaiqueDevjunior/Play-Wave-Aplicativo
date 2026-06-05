import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from api.v1.audio.categories import (
    create_audio_category,
    update_audio_category,
    _resolve_tenant_id,
)
from core.schemas_completos import AudioCategoryCreate, AudioCategoryUpdate
from crud.entidades.crud_audio_category import (
    crud_audio_category,
    default_categories,
    slugify,
    DEFAULT_CATEGORY_SLUGS,
)
from core.models import AudioCategory


class FakeCategoryQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None


class FakeCategorySession:
    def __init__(self, rows=None):
        self.rows = rows or []

    def query(self, model):
        if model is not AudioCategory:
            raise AssertionError(f"Unexpected query model: {model!r}")
        return FakeCategoryQuery(self.rows)


class SlugifyTest(unittest.TestCase):
    def test_slugify_handles_accents_and_spaces(self):
        self.assertEqual(slugify("Promoções de Verão"), "promocoes-de-verao")

    def test_slugify_collapses_special_chars(self):
        self.assertEqual(slugify("  Fim   de Semana!! "), "fim-de-semana")

    def test_slugify_empty_for_symbols_only(self):
        self.assertEqual(slugify("@#$%"), "")


class DefaultCategoriesTest(unittest.TestCase):
    def test_returns_five_defaults_all_marked_default(self):
        defaults = default_categories()
        self.assertEqual(len(defaults), 5)
        self.assertTrue(all(d["is_default"] for d in defaults))
        self.assertIsNone(defaults[0]["id"])

    def test_default_slugs_match_enum(self):
        slugs = {d["slug"] for d in default_categories()}
        self.assertEqual(slugs, DEFAULT_CATEGORY_SLUGS)


class SlugIsTakenTest(unittest.TestCase):
    def test_default_slug_is_always_taken(self):
        db = FakeCategorySession([])
        self.assertTrue(crud_audio_category.slug_is_taken(db, tenant_id="t1", slug="music"))

    def test_free_slug_returns_false(self):
        db = FakeCategorySession([])
        self.assertFalse(crud_audio_category.slug_is_taken(db, tenant_id="t1", slug="promocoes"))

    def test_existing_custom_slug_is_taken(self):
        existing = SimpleNamespace(id="cat-1", slug="promocoes", tenant_id="t1")
        db = FakeCategorySession([existing])
        self.assertTrue(crud_audio_category.slug_is_taken(db, tenant_id="t1", slug="promocoes"))

    def test_excludes_self_on_rename(self):
        existing = SimpleNamespace(id="cat-1", slug="promocoes", tenant_id="t1")
        db = FakeCategorySession([existing])
        self.assertFalse(
            crud_audio_category.slug_is_taken(
                db, tenant_id="t1", slug="promocoes", exclude_id="cat-1"
            )
        )


class ResolveTenantTest(unittest.TestCase):
    def test_non_admin_forced_to_own_tenant(self):
        user = SimpleNamespace(role="operator", tenant_id="own-tenant")
        self.assertEqual(_resolve_tenant_id(user, "other-tenant"), "own-tenant")

    def test_admin_can_pass_tenant(self):
        user = SimpleNamespace(role="admin", tenant_id=None)
        self.assertEqual(_resolve_tenant_id(user, "target"), "target")


class CreateCategoryEndpointTest(unittest.TestCase):
    def test_duplicate_name_raises_409(self):
        user = SimpleNamespace(role="admin", tenant_id=None)
        body = AudioCategoryCreate(name="Música", tenant_id="t1")
        with patch.object(crud_audio_category, "slug_is_taken", return_value=True):
            with self.assertRaises(HTTPException) as ctx:
                create_audio_category(db=MagicMock(), current_user=user, category_in=body)
        self.assertEqual(ctx.exception.status_code, 409)

    def test_invalid_name_raises_400(self):
        user = SimpleNamespace(role="admin", tenant_id=None)
        body = AudioCategoryCreate(name="@#$", tenant_id="t1")
        with self.assertRaises(HTTPException) as ctx:
            create_audio_category(db=MagicMock(), current_user=user, category_in=body)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_create_success_returns_slug(self):
        user = SimpleNamespace(role="admin", tenant_id=None)
        body = AudioCategoryCreate(name="Promoções", tenant_id="t1")
        created = AudioCategory(
            id=uuid.uuid4(), name="Promoções", slug="promocoes", tenant_id=None, is_default=False
        )
        with patch.object(crud_audio_category, "slug_is_taken", return_value=False), \
             patch.object(crud_audio_category, "create_for_tenant", return_value=created):
            result = create_audio_category(db=MagicMock(), current_user=user, category_in=body)
        self.assertEqual(result.slug, "promocoes")
        self.assertFalse(result.is_default)


class UpdateCategoryEndpointTest(unittest.TestCase):
    def test_update_missing_raises_404(self):
        user = SimpleNamespace(role="admin", tenant_id=None)
        body = AudioCategoryUpdate(name="Novo Nome")
        with patch.object(crud_audio_category, "get", return_value=None):
            with self.assertRaises(HTTPException) as ctx:
                update_audio_category(
                    db=MagicMock(), current_user=user, category_id="x", category_in=body
                )
        self.assertEqual(ctx.exception.status_code, 404)

    def test_update_other_tenant_forbidden(self):
        user = SimpleNamespace(role="operator", tenant_id="mine")
        body = AudioCategoryUpdate(name="Novo Nome")
        category = SimpleNamespace(id="cat-1", tenant_id="theirs")
        with patch.object(crud_audio_category, "get", return_value=category):
            with self.assertRaises(HTTPException) as ctx:
                update_audio_category(
                    db=MagicMock(), current_user=user, category_id="cat-1", category_in=body
                )
        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
