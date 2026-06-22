"""desktop_exposure_warning: aviso visual configuravel antes de minimizar (SPEC 015)

Revision ID: 20260618_1100
Revises: 20260607_1130
Create Date: 2026-06-18 11:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "20260618_1100"
down_revision = "20260607_1130"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "devices",
        sa.Column(
            "desktop_exposure_show_warning",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "devices",
        sa.Column("desktop_exposure_warning_seconds_before", sa.Integer(), nullable=True),
    )
    op.add_column(
        "devices",
        sa.Column("desktop_exposure_warning_text", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "devices",
        sa.Column(
            "desktop_exposure_warning_media_id",
            UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "ck_devices_desktop_exposure_warning_seconds",
        "devices",
        "(NOT desktop_exposure_show_warning) OR (desktop_exposure_warning_seconds_before BETWEEN 0 AND 120)",
    )


def downgrade():
    op.drop_constraint("ck_devices_desktop_exposure_warning_seconds", "devices", type_="check")
    op.drop_column("devices", "desktop_exposure_warning_media_id")
    op.drop_column("devices", "desktop_exposure_warning_text")
    op.drop_column("devices", "desktop_exposure_warning_seconds_before")
    op.drop_column("devices", "desktop_exposure_show_warning")
