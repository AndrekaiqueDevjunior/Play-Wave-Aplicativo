"""Add shuffle_enabled and loop_enabled to AudioFolder (TASK 06)

Revision ID: 20260604_1400
Revises: 20260604_1300
Create Date: 2026-06-04 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260604_1400"
down_revision = "20260604_1300"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('audio_folders', sa.Column('loop_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('audio_folders', sa.Column('shuffle_enabled', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('audio_folders', 'shuffle_enabled')
    op.drop_column('audio_folders', 'loop_enabled')
