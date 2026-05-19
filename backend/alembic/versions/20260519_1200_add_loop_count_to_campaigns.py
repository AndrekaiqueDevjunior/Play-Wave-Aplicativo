"""add_loop_count_to_campaigns

Revision ID: add_loop_count_to_campaigns
Revises: add_video_muted_to_campaigns
Create Date: 2026-05-19 12:00:00.000000

Adiciona o critério "rodar N voltas e parar".
loop_count NULL = infinito; N = parar após N passagens completas pela playlist.
Combina com end_date / schedule_end_time: para no que vier primeiro.
"""

from alembic import op
import sqlalchemy as sa


revision = "add_loop_count_to_campaigns"
down_revision = "add_video_muted_to_campaigns"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "campaigns",
        sa.Column("loop_count", sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_column("campaigns", "loop_count")
