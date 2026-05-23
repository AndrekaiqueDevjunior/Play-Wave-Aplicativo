"""create audio playback events

Revision ID: audio_playback_events
Revises: audio_spots
Create Date: 2026-05-23 16:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "audio_playback_events"
down_revision = "audio_spots"
branch_labels = None
depends_on = None


EVENT_TYPE_VALUES = ["track_started", "track_ended", "spot_started", "spot_ended", "error"]
RESULT_VALUES = ["success", "skipped", "failed", "interrupted"]


def upgrade():
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audio_playback_event_type') THEN
                CREATE TYPE audio_playback_event_type AS ENUM ('track_started', 'track_ended', 'spot_started', 'spot_ended', 'error');
            END IF;
        END$$
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audio_playback_result') THEN
                CREATE TYPE audio_playback_result AS ENUM ('success', 'skipped', 'failed', 'interrupted');
            END IF;
        END$$
        """
    )

    op.create_table(
        "audio_playback_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("playlist_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("spot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "event_type",
            postgresql.ENUM(
                *EVENT_TYPE_VALUES,
                name="audio_playback_event_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "result",
            postgresql.ENUM(
                *RESULT_VALUES,
                name="audio_playback_result",
                create_type=False,
            ),
            nullable=False,
            server_default="success",
        ),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["playlist_id"], ["audio_playlists.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["track_id"], ["audio_tracks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["spot_id"], ["audio_spots.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audio_playback_events_device_id", "audio_playback_events", ["device_id"])
    op.create_index("ix_audio_playback_events_playlist_id", "audio_playback_events", ["playlist_id"])
    op.create_index("ix_audio_playback_events_track_id", "audio_playback_events", ["track_id"])
    op.create_index("ix_audio_playback_events_spot_id", "audio_playback_events", ["spot_id"])
    op.create_index("ix_audio_playback_events_event_type", "audio_playback_events", ["event_type"])
    op.create_index(
        "ix_audio_playback_events_created_at",
        "audio_playback_events",
        ["created_at"],
    )
    op.create_index(
        "ix_audio_playback_events_device_created",
        "audio_playback_events",
        ["device_id", "created_at"],
    )


def downgrade():
    op.drop_index("ix_audio_playback_events_device_created", table_name="audio_playback_events")
    op.drop_index("ix_audio_playback_events_created_at", table_name="audio_playback_events")
    op.drop_index("ix_audio_playback_events_event_type", table_name="audio_playback_events")
    op.drop_index("ix_audio_playback_events_spot_id", table_name="audio_playback_events")
    op.drop_index("ix_audio_playback_events_track_id", table_name="audio_playback_events")
    op.drop_index("ix_audio_playback_events_playlist_id", table_name="audio_playback_events")
    op.drop_index("ix_audio_playback_events_device_id", table_name="audio_playback_events")
    op.drop_table("audio_playback_events")
    op.execute("DROP TYPE IF EXISTS audio_playback_result")
    op.execute("DROP TYPE IF EXISTS audio_playback_event_type")
