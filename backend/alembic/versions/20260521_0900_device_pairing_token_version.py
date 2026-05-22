"""add device pairing/token version controls

Revision ID: device_pairing_token_version
Revises: media_metadata_versions
Create Date: 2026-05-21 09:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "device_pairing_token_version"
down_revision = "media_metadata_versions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("devices", sa.Column("pairing_version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("devices", sa.Column("token_version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column(
        "devices",
        sa.Column("requires_repairing", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade():
    op.drop_column("devices", "requires_repairing")
    op.drop_column("devices", "token_version")
    op.drop_column("devices", "pairing_version")
