"""create audio playlist folder schedules

Revision ID: audio_playlist_folder_schedules
Revises: audio_folders
Create Date: 2026-05-23 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "audio_playlist_folder_schedules"
down_revision = "audio_folders"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'audio_playlist_play_mode') THEN
                CREATE TYPE audio_playlist_play_mode AS ENUM ('sequential', 'shuffle', 'loop');
            END IF;
        END$$
        """
    )

    op.create_table(
        "audio_playlist_folder_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("playlist_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("folder_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_time", sa.String(10), nullable=True),
        sa.Column("end_time", sa.String(10), nullable=True),
        sa.Column("starts_at", sa.DateTime(), nullable=True),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("days_of_week", postgresql.JSON(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "play_mode",
            postgresql.ENUM(
                "sequential",
                "shuffle",
                "loop",
                name="audio_playlist_play_mode",
                create_type=False,
            ),
            nullable=True,
            server_default="sequential",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["playlist_id"], ["audio_playlists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["folder_id"], ["audio_folders.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_audio_playlist_folder_schedules_playlist_id",
        "audio_playlist_folder_schedules",
        ["playlist_id"],
    )
    op.create_index(
        "ix_audio_playlist_folder_schedules_folder_id",
        "audio_playlist_folder_schedules",
        ["folder_id"],
    )
    op.create_index(
        "ix_audio_playlist_folder_schedules_time",
        "audio_playlist_folder_schedules",
        ["start_time", "end_time"],
    )


def downgrade():
    op.drop_index(
        "ix_audio_playlist_folder_schedules_time",
        table_name="audio_playlist_folder_schedules",
    )
    op.drop_index(
        "ix_audio_playlist_folder_schedules_folder_id",
        table_name="audio_playlist_folder_schedules",
    )
    op.drop_index(
        "ix_audio_playlist_folder_schedules_playlist_id",
        table_name="audio_playlist_folder_schedules",
    )
    op.drop_table("audio_playlist_folder_schedules")
    op.execute("DROP TYPE IF EXISTS audio_playlist_play_mode")
