"""CRUD de categorias de áudio personalizadas (TASK 02).

As 5 categorias padrão (music, jingle, announcement, ambient, other) continuam
existindo via o enum `AudioTrackCategory` e são expostas como entradas virtuais
(`is_default=True`, sem `id`). Esta camada cuida apenas das categorias custom
gravadas na tabela `audio_categories`, garantindo slug único por tenant.
"""

import re
import unicodedata
from typing import List, Optional

from sqlalchemy.orm import Session

from core.models import AudioCategory, AudioTrackCategory
from core.schemas_completos import AudioCategoryCreate, AudioCategoryUpdate
from .crud_base import CRUDBase


# Slugs reservados pelas categorias padrão (não podem ser duplicados por custom).
DEFAULT_CATEGORY_SLUGS = {item.value for item in AudioTrackCategory}

DEFAULT_CATEGORY_LABELS = {
    "music": "Música",
    "jingle": "Jingle",
    "announcement": "Anúncio",
    "ambient": "Ambiente",
    "other": "Outro",
}


def slugify(value: str) -> str:
    """Normaliza um nome para slug: minúsculas, sem acento, hífens."""
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_only = ascii_only.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return slug


def default_categories() -> List[dict]:
    """Lista as categorias padrão como entradas virtuais (is_default=True)."""
    return [
        {
            "id": None,
            "tenant_id": None,
            "name": DEFAULT_CATEGORY_LABELS.get(item.value, item.value.title()),
            "slug": item.value,
            "is_default": True,
            "created_at": None,
            "updated_at": None,
        }
        for item in AudioTrackCategory
    ]


class CRUDAudioCategory(CRUDBase[AudioCategory, AudioCategoryCreate, AudioCategoryUpdate]):
    def get_by_tenant(self, db: Session, *, tenant_id: Optional[str]) -> List[AudioCategory]:
        query = db.query(AudioCategory)
        if tenant_id is None:
            query = query.filter(AudioCategory.tenant_id.is_(None))
        else:
            query = query.filter(AudioCategory.tenant_id == tenant_id)
        return query.order_by(AudioCategory.name).all()

    def get_by_slug(
        self, db: Session, *, tenant_id: Optional[str], slug: str
    ) -> Optional[AudioCategory]:
        query = db.query(AudioCategory).filter(AudioCategory.slug == slug)
        if tenant_id is None:
            query = query.filter(AudioCategory.tenant_id.is_(None))
        else:
            query = query.filter(AudioCategory.tenant_id == tenant_id)
        return query.first()

    def slug_is_taken(
        self,
        db: Session,
        *,
        tenant_id: Optional[str],
        slug: str,
        exclude_id: Optional[str] = None,
    ) -> bool:
        """True se o slug já está em uso por uma categoria padrão ou custom do tenant."""
        if slug in DEFAULT_CATEGORY_SLUGS:
            return True
        existing = self.get_by_slug(db, tenant_id=tenant_id, slug=slug)
        if existing is None:
            return False
        if exclude_id is not None and str(existing.id) == str(exclude_id):
            return False
        return True

    def create_for_tenant(
        self, db: Session, *, name: str, tenant_id: Optional[str]
    ) -> AudioCategory:
        slug = slugify(name)
        category = AudioCategory(
            name=name.strip(),
            slug=slug,
            tenant_id=tenant_id,
            is_default=False,
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    def rename(self, db: Session, *, db_obj: AudioCategory, name: str) -> AudioCategory:
        db_obj.name = name.strip()
        db_obj.slug = slugify(name)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


crud_audio_category = CRUDAudioCategory(AudioCategory)
