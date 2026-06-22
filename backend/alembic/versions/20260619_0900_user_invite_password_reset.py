"""user_invite_password_reset: senha opcional + convite por e-mail + reset de senha (SPEC 019)

Revision ID: 20260619_0900
Revises: 20260618_1400
Create Date: 2026-06-19 09:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260619_0900"
down_revision = "20260618_1400"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=True)
    op.add_column("users", sa.Column("invite_token", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("invite_expires_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("invite_sent_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("password_reset_token", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("password_reset_expires_at", sa.DateTime(), nullable=True))
    op.create_unique_constraint("uq_users_invite_token", "users", ["invite_token"])
    op.create_unique_constraint("uq_users_password_reset_token", "users", ["password_reset_token"])
    op.create_index("ix_users_invite_token", "users", ["invite_token"])
    op.create_index("ix_users_password_reset_token", "users", ["password_reset_token"])
    op.execute("ALTER TYPE userlogaction ADD VALUE IF NOT EXISTS 'resend_invite'")
    op.execute("ALTER TYPE userlogaction ADD VALUE IF NOT EXISTS 'accept_invite'")


def downgrade():
    # Nota: remover valores de enum Postgres requer recriar o tipo
    # (não há DROP VALUE nativo). Não revertido aqui — mesma limitação
    # documentada na migration 20260618_1400.
    op.drop_index("ix_users_password_reset_token", table_name="users")
    op.drop_index("ix_users_invite_token", table_name="users")
    op.drop_constraint("uq_users_password_reset_token", "users", type_="unique")
    op.drop_constraint("uq_users_invite_token", "users", type_="unique")
    op.drop_column("users", "password_reset_expires_at")
    op.drop_column("users", "password_reset_token")
    op.drop_column("users", "invite_sent_at")
    op.drop_column("users", "invite_expires_at")
    op.drop_column("users", "invite_token")
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=False)
