"""add_video_muted_to_campaigns

Revision ID: add_video_muted_to_campaigns
Revises: 317950e57223
Create Date: 2026-05-18 21:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "add_video_muted_to_campaigns"
down_revision = "317950e57223"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "campaigns",
        sa.Column("video_muted", sa.Boolean(), nullable=True, server_default=sa.text("true")),
    )


def downgrade():
    op.drop_column("campaigns", "video_muted")
