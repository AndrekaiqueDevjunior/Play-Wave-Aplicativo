"""add device_commands table

Revision ID: 002
Revises: 001
Create Date: 2026-05-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    device_command_status_enum = postgresql.ENUM(
        "pending", "sent", "executed", "failed", "cancelled",
        name="devicecommandstatus",
    )
    device_command_status_enum.create(op.get_bind())

    op.create_table(
        "device_commands",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("command_type", sa.String(50), nullable=False),
        sa.Column("payload", postgresql.JSON(), nullable=True),
        sa.Column(
            "status",
            device_command_status_enum,
            nullable=True,
            server_default="pending",
        ),
        sa.Column("requested_by", sa.String(255), nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )

    op.create_index("ix_device_commands_device_id", "device_commands", ["device_id"])
    op.create_index("ix_device_commands_status", "device_commands", ["status"])


def downgrade():
    op.drop_index("ix_device_commands_status", table_name="device_commands")
    op.drop_index("ix_device_commands_device_id", table_name="device_commands")
    op.drop_table("device_commands")
    postgresql.ENUM(name="devicecommandstatus").drop(op.get_bind())
