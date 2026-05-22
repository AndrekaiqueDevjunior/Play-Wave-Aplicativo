"""merge heads after SPEC 003

Revision ID: merge_heads_20260522
Revises: command_defaults_and_index, campaign_playlist_items
Create Date: 2026-05-22 11:00:00.000000

Antes da SPEC 003 já havia duas linhas paralelas a partir de
`media_metadata_versions`:

  media_metadata_versions
    ├── campaign_playlist_items (branch das mídias relacionais)
    └── device_pairing_token_version
          └── device_command_lifecycle
                └── command_defaults_and_index (SPEC 003)

Sem este merge, `alembic upgrade head` falha porque há múltiplos heads. Esta
migration não faz alterações — apenas une os dois ramos para deixar a chain
linear novamente.
"""

from alembic import op
import sqlalchemy as sa


revision = "merge_heads_20260522"
down_revision = ("command_defaults_and_index", "campaign_playlist_items")
branch_labels = None
depends_on = None


def upgrade():
    # Merge migration — sem alterações de schema.
    pass


def downgrade():
    pass
