"""create audio spots and spot schedules

Revision ID: audio_spots
Revises: audio_playlist_folder_schedules
Create Date: 2026-05-23 15:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "audio_spots"
down_revision = "audio_playlist_folder_schedules"
branch_labels = None
depends_on = None


AUDIO_SPOT_STATUS_VALUES = ["active", "inactive", "archived"]
AUDIO_SPOT_INSERTION_POLICY_VALUES = ["interrupt", "wait_silence", "fade_mix"]


def upgrade():
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audio_spot_status') THEN
                CREATE TYPE audio_spot_status AS ENUM ('active', 'inactive', 'archived');
            END IF;
        END$$
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audio_spot_insertion_policy') THEN
                CREATE TYPE audio_spot_insertion_policy AS ENUM ('interrupt', 'wait_silence', 'fade_mix');
            END IF;
        END$$
        """
    )

    op.create_table(
        "audio_spots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                *AUDIO_SPOT_STATUS_VALUES,
                name="audio_spot_status",
                create_type=False,
            ),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "insertion_policy",
            postgresql.ENUM(
                *AUDIO_SPOT_INSERTION_POLICY_VALUES,
                name="audio_spot_insertion_policy",
                create_type=False,
            ),
            nullable=False,
            server_default="wait_silence",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["track_id"], ["audio_tracks.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_audio_spots_tenant_id", "audio_spots", ["tenant_id"])
    op.create_index("ix_audio_spots_track_id", "audio_spots", ["track_id"])
    op.create_index("ix_audio_spots_status", "audio_spots", ["status"])

    op.create_table(
        "audio_spot_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("spot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("playlist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interval_seconds", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.String(10), nullable=True),
        sa.Column("end_time", sa.String(10), nullable=True),
        sa.Column("starts_at", sa.DateTime(), nullable=True),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["spot_id"], ["audio_spots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["playlist_id"], ["audio_playlists.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("spot_id", "playlist_id", name="uq_audio_spot_schedules_spot_playlist"),
    )
    op.create_index("ix_audio_spot_schedules_spot_id", "audio_spot_schedules", ["spot_id"])
    op.create_index("ix_audio_spot_schedules_playlist_id", "audio_spot_schedules", ["playlist_id"])
    op.create_index(
        "ix_audio_spot_schedules_time",
        "audio_spot_schedules",
        ["start_time", "end_time"],
    )


def downgrade():
    op.drop_index(
        "ix_audio_spot_schedules_time",
        table_name="audio_spot_schedules",
    )
    op.drop_index(
        "ix_audio_spot_schedules_playlist_id",
        table_name="audio_spot_schedules",
    )
    op.drop_index("ix_audio_spot_schedules_spot_id", table_name="audio_spot_schedules")
    op.drop_table("audio_spot_schedules")

    op.drop_index("ix_audio_spots_status", table_name="audio_spots")
    op.drop_index("ix_audio_spots_track_id", table_name="audio_spots")
    op.drop_index("ix_audio_spots_tenant_id", table_name="audio_spots")
    op.drop_table("audio_spots")

    op.execute("DROP TYPE IF EXISTS audio_spot_insertion_policy")
    op.execute("DROP TYPE IF EXISTS audio_spot_status")
