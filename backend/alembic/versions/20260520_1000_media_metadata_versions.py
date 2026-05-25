"""add media metadata, validity window, and versions

Revision ID: media_metadata_versions
Revises: add_loop_count_to_campaigns
Create Date: 2026-05-20 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "media_metadata_versions"
down_revision = "add_loop_count_to_campaigns"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("media", sa.Column("duration_seconds", sa.Integer(), nullable=True))
    op.add_column("media", sa.Column("display_duration_seconds", sa.Integer(), nullable=True))
    op.add_column("media", sa.Column("file_hash", sa.String(length=128), nullable=True))
    op.add_column("media", sa.Column("file_version", sa.Integer(), nullable=True, server_default="1"))
    op.add_column("media", sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("true")))
    op.add_column("media", sa.Column("starts_at", sa.DateTime(), nullable=True))
    op.add_column("media", sa.Column("ends_at", sa.DateTime(), nullable=True))
    op.add_column("media", sa.Column("extra_metadata", postgresql.JSON(), nullable=True))
    op.add_column("media", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("media", sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_media_created_by_users", "media", "users", ["created_by"], ["id"])
    op.create_foreign_key("fk_media_updated_by_users", "media", "users", ["updated_by"], ["id"])
    op.create_index("ix_media_starts_at", "media", ["starts_at"])
    op.create_index("ix_media_ends_at", "media", ["ends_at"])
    op.create_index("ix_media_file_hash", "media", ["file_hash"])

    op.execute("UPDATE media SET duration_seconds = duration WHERE duration_seconds IS NULL")
    # SQLAlchemy stores enum values as the member NAME (uppercase), so the
    # comparison must use the uppercase enum labels.
    op.execute("UPDATE media SET display_duration_seconds = duration WHERE display_duration_seconds IS NULL AND type IN ('IMAGE', 'EXTERNAL_URL')")

    op.create_table(
        "media_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("media_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=False),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("file_hash", sa.String(length=128), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_current", sa.Boolean(), nullable=True, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )
    op.create_index("ix_media_versions_media_id", "media_versions", ["media_id"])


def downgrade():
    op.drop_index("ix_media_versions_media_id", table_name="media_versions")
    op.drop_table("media_versions")
    op.drop_index("ix_media_file_hash", table_name="media")
    op.drop_index("ix_media_ends_at", table_name="media")
    op.drop_index("ix_media_starts_at", table_name="media")
    op.drop_constraint("fk_media_updated_by_users", "media", type_="foreignkey")
    op.drop_constraint("fk_media_created_by_users", "media", type_="foreignkey")
    op.drop_column("media", "updated_by")
    op.drop_column("media", "created_by")
    op.drop_column("media", "extra_metadata")
    op.drop_column("media", "ends_at")
    op.drop_column("media", "starts_at")
    op.drop_column("media", "is_active")
    op.drop_column("media", "file_version")
    op.drop_column("media", "file_hash")
    op.drop_column("media", "display_duration_seconds")
    op.drop_column("media", "duration_seconds")
