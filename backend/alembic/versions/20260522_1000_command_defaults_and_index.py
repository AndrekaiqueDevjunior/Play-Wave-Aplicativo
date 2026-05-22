"""command defaults and index (SPEC 003)

Revision ID: command_defaults_and_index
Revises: device_command_lifecycle
Create Date: 2026-05-22 10:00:00.000000

Adiciona coluna is_destructive em device_commands + indice composto para
otimizar a query de comandos pendentes do player. SPEC 003 — Player Comandos
Nativos.
"""

from alembic import op
import sqlalchemy as sa


revision = "command_defaults_and_index"
down_revision = "device_command_lifecycle"
branch_labels = None
depends_on = None


DESTRUCTIVE_COMMANDS = (
    "restart_app",
    "restart_device",
    "shutdown_device",
    "factory_reset",
    "reboot",
)


def upgrade():
    op.add_column(
        "device_commands",
        sa.Column(
            "is_destructive",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # Backfill historico.
    placeholders = ", ".join(f"'{c}'" for c in DESTRUCTIVE_COMMANDS)
    op.execute(
        f"UPDATE device_commands SET is_destructive = TRUE "
        f"WHERE command_type IN ({placeholders})"
    )

    # Indice parcial para acelerar a query de pending/sent/received/executing
    # filtrada por expires_at futuro. Indices parciais nao sao suportados em
    # todos os bancos; em SQLite/MySQL o WHERE eh ignorado e o indice eh full.
    bind = op.get_bind()
    dialect = bind.dialect.name if bind else "postgresql"
    if dialect == "postgresql":
        # Valores do enum no DB são UPPERCASE (member.name do SQLAlchemy),
        # não os values em lowercase do Python enum.
        op.execute(
            "CREATE INDEX ix_device_commands_device_status_expires "
            "ON device_commands (device_id, status, expires_at) "
            "WHERE status IN ('PENDING', 'SENT', 'RECEIVED', 'EXECUTING')"
        )
    else:
        op.create_index(
            "ix_device_commands_device_status_expires",
            "device_commands",
            ["device_id", "status", "expires_at"],
        )


def downgrade():
    op.drop_index("ix_device_commands_device_status_expires", table_name="device_commands")
    op.drop_column("device_commands", "is_destructive")
