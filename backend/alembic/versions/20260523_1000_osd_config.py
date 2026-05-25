"""osd_config: tenant/device OSD settings and current audio track (SPEC 006)

Revision ID: osd_config
Revises: audio_policy
Create Date: 2026-05-23 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "osd_config"
down_revision = "audio_policy"
branch_labels = None
depends_on = None

OSD_POSITIONS = ["top_left", "top_right", "bottom_left", "bottom_right"]
OSD_FONT_SIZES = ["small", "medium", "large"]


def upgrade():
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'osd_position_enum') THEN
                CREATE TYPE osd_position_enum AS ENUM
                    ('top_left', 'top_right', 'bottom_left', 'bottom_right');
            END IF;
        END$$
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'osd_font_size_enum') THEN
                CREATE TYPE osd_font_size_enum AS ENUM ('small', 'medium', 'large');
            END IF;
        END$$
        """
    )

    op.add_column(
        "tenants",
        sa.Column("osd_show_current_audio", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "tenants",
        sa.Column(
            "osd_position",
            postgresql.ENUM(*OSD_POSITIONS, name="osd_position_enum", create_type=False),
            nullable=False,
            server_default="top_right",
        ),
    )
    op.add_column(
        "tenants",
        sa.Column("osd_duration_seconds", sa.Integer(), nullable=False, server_default="8"),
    )
    op.add_column(
        "tenants",
        sa.Column("osd_opacity", sa.Numeric(3, 2), nullable=False, server_default="0.6"),
    )
    op.add_column(
        "tenants",
        sa.Column(
            "osd_font_size",
            postgresql.ENUM(*OSD_FONT_SIZES, name="osd_font_size_enum", create_type=False),
            nullable=False,
            server_default="medium",
        ),
    )

    op.add_column("devices", sa.Column("osd_show_current_audio", sa.Boolean(), nullable=True))
    op.add_column(
        "devices",
        sa.Column(
            "osd_position",
            postgresql.ENUM(*OSD_POSITIONS, name="osd_position_enum", create_type=False),
            nullable=True,
        ),
    )
    op.add_column("devices", sa.Column("osd_duration_seconds", sa.Integer(), nullable=True))
    op.add_column("devices", sa.Column("osd_opacity", sa.Numeric(3, 2), nullable=True))
    op.add_column(
        "devices",
        sa.Column(
            "osd_font_size",
            postgresql.ENUM(*OSD_FONT_SIZES, name="osd_font_size_enum", create_type=False),
            nullable=True,
        ),
    )
    op.add_column("devices", sa.Column("current_audio_track_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("devices", sa.Column("current_audio_track_name", sa.String(500), nullable=True))
    op.add_column("devices", sa.Column("current_audio_track_started_at", sa.DateTime(timezone=True), nullable=True))

    op.create_check_constraint(
        "ck_tenants_osd_duration_seconds",
        "tenants",
        "osd_duration_seconds BETWEEN 0 AND 3600",
    )
    op.create_check_constraint(
        "ck_tenants_osd_opacity",
        "tenants",
        "osd_opacity BETWEEN 0 AND 1",
    )
    op.create_check_constraint(
        "ck_devices_osd_duration_seconds",
        "devices",
        "osd_duration_seconds IS NULL OR osd_duration_seconds BETWEEN 0 AND 3600",
    )
    op.create_check_constraint(
        "ck_devices_osd_opacity",
        "devices",
        "osd_opacity IS NULL OR osd_opacity BETWEEN 0 AND 1",
    )


def downgrade():
    op.drop_constraint("ck_devices_osd_opacity", "devices", type_="check")
    op.drop_constraint("ck_devices_osd_duration_seconds", "devices", type_="check")
    op.drop_constraint("ck_tenants_osd_opacity", "tenants", type_="check")
    op.drop_constraint("ck_tenants_osd_duration_seconds", "tenants", type_="check")

    op.drop_column("devices", "current_audio_track_started_at")
    op.drop_column("devices", "current_audio_track_name")
    op.drop_column("devices", "current_audio_track_id")
    op.drop_column("devices", "osd_font_size")
    op.drop_column("devices", "osd_opacity")
    op.drop_column("devices", "osd_duration_seconds")
    op.drop_column("devices", "osd_position")
    op.drop_column("devices", "osd_show_current_audio")

    op.drop_column("tenants", "osd_font_size")
    op.drop_column("tenants", "osd_opacity")
    op.drop_column("tenants", "osd_duration_seconds")
    op.drop_column("tenants", "osd_position")
    op.drop_column("tenants", "osd_show_current_audio")

    op.execute("DROP TYPE osd_font_size_enum")
    op.execute("DROP TYPE osd_position_enum")
