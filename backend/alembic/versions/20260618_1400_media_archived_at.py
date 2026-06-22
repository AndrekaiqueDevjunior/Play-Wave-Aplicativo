"""media_archived_at: estado ARCHIVED + timestamp de arquivamento para midias (SPEC 018)

Revision ID: 20260618_1400
Revises: 20260618_1300
Create Date: 2026-06-18 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260618_1400"
down_revision = "20260618_1300"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TYPE mediastatus ADD VALUE IF NOT EXISTS 'archived'")
    op.add_column(
        "media",
        sa.Column("archived_at", sa.DateTime(), nullable=True),
    )
    # Backfill: não aplicável aqui — antes desta migration o status
    # 'archived' não existia no enum, então não há linhas pré-existentes
    # com esse valor para retroagir o timestamp.


def downgrade():
    op.drop_column("media", "archived_at")
    # Nota: remover um valor de enum Postgres requer recriar o tipo
    # (não há DROP VALUE nativo). Não revertido aqui — mesma limitação
    # documentada nas migrations anteriores que adicionam valores de enum.
