"""desktop_exposure_config: per-device desktop exposure settings (SPEC 009)

Revision ID: 20260601_1800
Revises: audio_playback_events
Create Date: 2026-06-01 18:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260601_1800"
down_revision = "audio_playback_events"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "devices",
        sa.Column("desktop_exposure_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "devices",
        sa.Column("desktop_exposure_interval_seconds", sa.Integer(), nullable=True),
    )
    op.add_column(
        "devices",
        sa.Column("desktop_exposure_duration_seconds", sa.Integer(), nullable=True),
    )
    op.add_column(
        "devices",
        sa.Column(
            "desktop_exposure_restore_fullscreen",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )
    op.add_column(
        "devices",
        sa.Column("desktop_exposure_updated_at", sa.DateTime(), nullable=True),
    )

    op.create_check_constraint(
        "ck_devices_desktop_exposure_timing",
        "devices",
        "(NOT desktop_exposure_enabled) OR (desktop_exposure_interval_seconds BETWEEN 10 AND 86400 AND desktop_exposure_duration_seconds BETWEEN 1 AND 300 AND desktop_exposure_duration_seconds < desktop_exposure_interval_seconds)",
    )


def downgrade():
    op.drop_constraint("ck_devices_desktop_exposure_timing", "devices", type_="check")
    op.drop_column("devices", "desktop_exposure_updated_at")
    op.drop_column("devices", "desktop_exposure_restore_fullscreen")
    op.drop_column("devices", "desktop_exposure_duration_seconds")
    op.drop_column("devices", "desktop_exposure_interval_seconds")
    op.drop_column("devices", "desktop_exposure_enabled")
