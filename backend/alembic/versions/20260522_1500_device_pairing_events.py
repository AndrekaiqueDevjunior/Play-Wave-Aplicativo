"""device_pairing_events table (SPEC 004)

Revision ID: device_pairing_events
Revises: merge_heads_20260522
Create Date: 2026-05-22 15:00:00.000000

Cria a tabela de auditoria de eventos de pareamento. Toda regeneracao de
codigo, force-repair, bloqueio, etc. gera uma linha aqui com previous/new
versions, requested_by e reason. Sem backfill — historico anterior nao eh
reconstrutivel.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "device_pairing_events"
down_revision = "merge_heads_20260522"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "device_pairing_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "device_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("devices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(40), nullable=False),
        sa.Column("previous_token_version", sa.Integer(), nullable=True),
        sa.Column("new_token_version", sa.Integer(), nullable=True),
        sa.Column("previous_pairing_version", sa.Integer(), nullable=True),
        sa.Column("new_pairing_version", sa.Integer(), nullable=True),
        sa.Column("previous_pairing_code", sa.String(40), nullable=True),
        sa.Column("new_pairing_code", sa.String(40), nullable=True),
        sa.Column(
            "requested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index(
        "ix_device_pairing_events_device_id_created_at",
        "device_pairing_events",
        ["device_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_device_pairing_events_event_type",
        "device_pairing_events",
        ["event_type"],
    )


def downgrade():
    op.drop_index("ix_device_pairing_events_event_type", table_name="device_pairing_events")
    op.drop_index("ix_device_pairing_events_device_id_created_at", table_name="device_pairing_events")
    op.drop_table("device_pairing_events")
