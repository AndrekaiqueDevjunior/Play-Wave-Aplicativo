"""create campaign_playlist_items and backfill from media_order/media_ids

Revision ID: campaign_playlist_items
Revises: media_metadata_versions
Create Date: 2026-05-20 14:00:00.000000
"""

import json
import uuid
from datetime import datetime

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "campaign_playlist_items"
down_revision = "media_metadata_versions"
branch_labels = None
depends_on = None


ORDER_STEP = 10


def upgrade():
    op.create_table(
        "campaign_playlist_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("media_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("display_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("starts_at", sa.DateTime(), nullable=True),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("repeat_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=True, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["media_id"], ["media.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_campaign_playlist_items_campaign_id",
        "campaign_playlist_items",
        ["campaign_id"],
    )
    op.create_index(
        "ix_campaign_playlist_items_media_id",
        "campaign_playlist_items",
        ["media_id"],
    )
    op.create_index(
        "ix_campaign_playlist_items_campaign_order",
        "campaign_playlist_items",
        ["campaign_id", "order_index"],
    )

    if context.is_offline_mode():
        # SQL dump mode: cannot run row-by-row backfill without a live connection.
        return
    _backfill_from_legacy_columns()


def _backfill_from_legacy_columns():
    """Backfill campaign_playlist_items from existing media_order / media_ids JSON columns."""
    bind = op.get_bind()
    campaigns = bind.execute(
        sa.text("SELECT id, media_ids, media_order FROM campaigns")
    ).fetchall()

    valid_media_ids = {
        str(row[0])
        for row in bind.execute(sa.text("SELECT id FROM media")).fetchall()
    }

    insert_sql = sa.text(
        """
        INSERT INTO campaign_playlist_items (
            id, campaign_id, media_id, order_index,
            display_duration_seconds, is_active, repeat_count,
            created_at, updated_at
        ) VALUES (
            :id, :campaign_id, :media_id, :order_index,
            :display_duration_seconds, :is_active, :repeat_count,
            :created_at, :updated_at
        )
        """
    )

    now = datetime.utcnow()

    for campaign_id, media_ids_json, media_order_json in campaigns:
        media_order = _coerce_json(media_order_json)
        media_ids = _coerce_json(media_ids_json)

        if media_order and isinstance(media_order, list):
            entries = []
            for item in media_order:
                if isinstance(item, dict):
                    mid = item.get("media_id")
                    duration = item.get("duration")
                else:
                    mid = item
                    duration = None
                if not mid or str(mid) not in valid_media_ids:
                    continue
                entries.append((str(mid), duration))
        elif media_ids and isinstance(media_ids, list):
            entries = [
                (str(mid), None)
                for mid in media_ids
                if mid and str(mid) in valid_media_ids
            ]
        else:
            entries = []

        for position, (mid, duration) in enumerate(entries):
            bind.execute(
                insert_sql,
                {
                    "id": str(uuid.uuid4()),
                    "campaign_id": str(campaign_id),
                    "media_id": mid,
                    "order_index": position * ORDER_STEP,
                    "display_duration_seconds": int(duration)
                    if isinstance(duration, (int, float)) and duration and duration > 0
                    else None,
                    "is_active": True,
                    "repeat_count": 1,
                    "created_at": now,
                    "updated_at": now,
                },
            )


def _coerce_json(value):
    """Driver-agnostic JSON coercion: psycopg may return parsed list/dict or raw string."""
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return None
    return None


def downgrade():
    op.drop_index(
        "ix_campaign_playlist_items_campaign_order",
        table_name="campaign_playlist_items",
    )
    op.drop_index(
        "ix_campaign_playlist_items_media_id",
        table_name="campaign_playlist_items",
    )
    op.drop_index(
        "ix_campaign_playlist_items_campaign_id",
        table_name="campaign_playlist_items",
    )
    op.drop_table("campaign_playlist_items")
