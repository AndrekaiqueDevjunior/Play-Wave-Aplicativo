"""add days_of_week to audio_spot_schedules

Revision ID: 20260606_1200
Revises: 20260605_1930_418d6a2b791c
Create Date: 2026-06-06 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '20260606_1200'
down_revision = '418d6a2b791c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'audio_spot_schedules',
        sa.Column('days_of_week', sa.JSON(), nullable=True)
    )


def downgrade():
    op.drop_column('audio_spot_schedules', 'days_of_week')
