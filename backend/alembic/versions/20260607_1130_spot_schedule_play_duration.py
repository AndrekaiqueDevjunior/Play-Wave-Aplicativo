"""AudioSpotSchedule: adiciona play_duration_seconds

NULL = tocar música inteira
N    = parar após N segundos (corte programado)

Revision ID: 20260607_1130
Revises: 20260606_1900_spot_schedule_schema_alignment
Create Date: 2026-06-07
"""
from alembic import op
import sqlalchemy as sa

revision = "20260607_1130"
down_revision = "20260606_1900"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "audio_spot_schedules",
        sa.Column("play_duration_seconds", sa.Integer(), nullable=True),
    )


def downgrade():
    op.drop_column("audio_spot_schedules", "play_duration_seconds")
