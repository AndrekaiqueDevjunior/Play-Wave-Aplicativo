"""audio_track_archived_at: timestamp de arquivamento de faixas (SPEC 016)

Revision ID: 20260618_1200
Revises: 20260618_1100
Create Date: 2026-06-18 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260618_1200"
down_revision = "20260618_1100"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "audio_tracks",
        sa.Column("archived_at", sa.DateTime(), nullable=True),
    )
    # Backfill: faixas já arquivadas antes desta migration recebem o
    # timestamp da migration como aproximação — melhor que None para quem
    # for ordenar/exibir "arquivada em X" na UI.
    op.execute(
        "UPDATE audio_tracks SET archived_at = now() WHERE status = 'archived' AND archived_at IS NULL"
    )


def downgrade():
    op.drop_column("audio_tracks", "archived_at")
