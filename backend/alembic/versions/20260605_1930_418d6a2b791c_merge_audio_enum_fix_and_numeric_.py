"""merge audio enum fix and numeric versioning branches

Revision ID: 418d6a2b791c
Revises: fix_audio_enum_case, 20260604_1600
Create Date: 2026-06-05 19:30:26.082439

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '418d6a2b791c'
down_revision = ('fix_audio_enum_case', '20260604_1600')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
