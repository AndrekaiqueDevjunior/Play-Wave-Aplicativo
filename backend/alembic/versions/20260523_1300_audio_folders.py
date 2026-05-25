"""create audio folders and folder track membership

Revision ID: audio_folders
Revises: audio_playlist_items
Create Date: 2026-05-23 13:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "audio_folders"
down_revision = "audio_playlist_items"
branch_labels = None
depends_on = None


AUDIO_FOLDER_STATUS_VALUES = ["active", "inactive", "archived"]


def upgrade():
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audio_folder_status') THEN
                CREATE TYPE audio_folder_status AS ENUM ('active', 'inactive', 'archived');
            END IF;
        END$$
        """
    )

    op.create_table(
        "audio_folders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                *AUDIO_FOLDER_STATUS_VALUES,
                name="audio_folder_status",
                create_type=False,
            ),
            nullable=True,
            server_default="active",
        ),
        sa.Column("starts_at", sa.DateTime(), nullable=True),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("start_time", sa.String(10), nullable=True),
        sa.Column("end_time", sa.String(10), nullable=True),
        sa.Column("schedule_days", postgresql.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audio_folders_tenant_id", "audio_folders", ["tenant_id"])
    op.create_index("ix_audio_folders_status", "audio_folders", ["status"])
    op.create_index("ix_audio_folders_period", "audio_folders", ["starts_at", "ends_at"])

    op.create_table(
        "audio_folder_tracks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("folder_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("volume_override", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["folder_id"], ["audio_folders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["track_id"], ["audio_tracks.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("folder_id", "track_id", name="uq_audio_folder_tracks_folder_track"),
    )
    op.create_index("ix_audio_folder_tracks_folder_id", "audio_folder_tracks", ["folder_id"])
    op.create_index("ix_audio_folder_tracks_track_id", "audio_folder_tracks", ["track_id"])
    op.create_index(
        "ix_audio_folder_tracks_folder_order",
        "audio_folder_tracks",
        ["folder_id", "order_index"],
    )


def downgrade():
    op.drop_index("ix_audio_folder_tracks_folder_order", table_name="audio_folder_tracks")
    op.drop_index("ix_audio_folder_tracks_track_id", table_name="audio_folder_tracks")
    op.drop_index("ix_audio_folder_tracks_folder_id", table_name="audio_folder_tracks")
    op.drop_table("audio_folder_tracks")

    op.drop_index("ix_audio_folders_period", table_name="audio_folders")
    op.drop_index("ix_audio_folders_status", table_name="audio_folders")
    op.drop_index("ix_audio_folders_tenant_id", table_name="audio_folders")
    op.drop_table("audio_folders")
    op.execute("DROP TYPE IF EXISTS audio_folder_status")
