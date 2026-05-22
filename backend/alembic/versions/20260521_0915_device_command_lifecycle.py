"""expand device command lifecycle

Revision ID: device_command_lifecycle
Revises: device_pairing_token_version
Create Date: 2026-05-21 09:15:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "device_command_lifecycle"
down_revision = "device_pairing_token_version"
branch_labels = None
depends_on = None


def upgrade():
    # Os valores do enum no PostgreSQL refletem o NOME dos membros do enum
    # Python (DeviceCommandStatus.RECEIVED -> "RECEIVED"), porque o SQLAlchemy
    # bind/convert usa `member.name` por padrão. Por isso UPPERCASE aqui.
    for value in ("RECEIVED", "EXECUTING", "COMPLETED", "EXPIRED"):
        op.execute(f"ALTER TYPE devicecommandstatus ADD VALUE IF NOT EXISTS '{value}'")

    op.add_column("device_commands", sa.Column("received_at", sa.DateTime(), nullable=True))
    op.add_column("device_commands", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("device_commands", sa.Column("expires_at", sa.DateTime(), nullable=True))
    op.add_column("device_commands", sa.Column("result", postgresql.JSON(), nullable=True))


def downgrade():
    op.drop_column("device_commands", "result")
    op.drop_column("device_commands", "expires_at")
    op.drop_column("device_commands", "started_at")
    op.drop_column("device_commands", "received_at")
