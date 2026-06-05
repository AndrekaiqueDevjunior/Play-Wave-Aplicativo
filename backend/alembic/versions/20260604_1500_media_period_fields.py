"""Add period fields to media (TASK 17)

Revision ID: 20260604_1500
Revises: 20260604_1400
Create Date: 2026-06-04 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260604_1500"
down_revision = "20260604_1400"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('media', sa.Column('start_time', sa.String(10), nullable=True))
    op.add_column('media', sa.Column('end_time', sa.String(10), nullable=True))
    op.add_column('media', sa.Column('days_of_week', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('media', 'days_of_week')
    op.drop_column('media', 'end_time')
    op.drop_column('media', 'start_time')
