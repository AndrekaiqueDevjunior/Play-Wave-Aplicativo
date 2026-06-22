"""audio_playlist_archived_at: timestamp de arquivamento de playlists sonoras (SPEC 017)

Revision ID: 20260618_1300
Revises: 20260618_1200
Create Date: 2026-06-18 13:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260618_1300"
down_revision = "20260618_1200"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "audio_playlists",
        sa.Column("archived_at", sa.DateTime(), nullable=True),
    )
    # Backfill: playlists já arquivadas antes desta migration recebem o
    # timestamp da migration como aproximação (mesma estratégia da SPEC 016
    # para audio_tracks).
    op.execute(
        "UPDATE audio_playlists SET archived_at = now() WHERE status = 'archived' AND archived_at IS NULL"
    )


def downgrade():
    op.drop_column("audio_playlists", "archived_at")
