"""audio_category_links: link categoria a pastas e playlists (TASK 02c)

Revision ID: 20260604_1300
Revises: 20260604_1200
Create Date: 2026-06-04 13:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260604_1300"
down_revision = "20260604_1200"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("audio_folders", "audio_playlists"):
        op.add_column(
            table,
            sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            f"fk_{table}_category_id",
            table,
            "audio_categories",
            ["category_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(f"ix_{table}_category_id", table, ["category_id"])


def downgrade():
    for table in ("audio_folders", "audio_playlists"):
        op.drop_index(f"ix_{table}_category_id", table_name=table)
        op.drop_constraint(f"fk_{table}_category_id", table, type_="foreignkey")
        op.drop_column(table, "category_id")
