"""audio_categories: custom per-tenant audio categories (TASK 02)

Revision ID: 20260604_1200
Revises: 20260601_1800
Create Date: 2026-06-04 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260604_1200"
down_revision = "20260601_1800"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audio_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_audio_categories_tenant_slug"),
    )
    op.create_index("ix_audio_categories_tenant_id", "audio_categories", ["tenant_id"])
    op.create_index("ix_audio_categories_slug", "audio_categories", ["slug"])

    op.add_column(
        "audio_tracks",
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_audio_tracks_category_id",
        "audio_tracks",
        "audio_categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_audio_tracks_category_id", "audio_tracks", ["category_id"])


def downgrade():
    op.drop_index("ix_audio_tracks_category_id", table_name="audio_tracks")
    op.drop_constraint("fk_audio_tracks_category_id", "audio_tracks", type_="foreignkey")
    op.drop_column("audio_tracks", "category_id")

    op.drop_index("ix_audio_categories_slug", table_name="audio_categories")
    op.drop_index("ix_audio_categories_tenant_id", table_name="audio_categories")
    op.drop_table("audio_categories")
